"""HQSPG extractor module.

Implements sample extraction from repaired stems:
- silence trimming
- transient detection (frame RMS peaks)
- zero-crossing alignment
- min/max slice length enforcement

Writes slices to <output_base>/<track_name>/samples/<stem>/ and returns
metadata objects for each slice.
"""
from typing import Dict, List, Any, Optional
import os
import wave
import logging
import numpy as np

logger = logging.getLogger(__name__)


def _read_wav(path: str):
    with wave.open(path, 'rb') as wf:
        nchan = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fr = wf.getframerate()
        nframes = wf.getnframes()
        data = wf.readframes(nframes)
    dtype = np.int16 if sampwidth == 2 else np.int16
    audio = np.frombuffer(data, dtype=dtype).astype(np.float32)
    if nchan > 1:
        audio = audio.reshape(-1, nchan).mean(axis=1)
    audio = audio / (np.iinfo(np.int16).max if dtype == np.int16 else 1.0)
    return audio, fr


def _write_wav(path: str, audio: np.ndarray, sr: int):
    clipped = np.clip(audio, -1.0, 1.0)
    int16 = (clipped * np.iinfo(np.int16).max).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16.tobytes())


def _frame_rms(x: np.ndarray, frame_size: int = 1024, hop: int = 512):
    frames = []
    for i in range(0, max(1, len(x) - frame_size + 1), hop):
        f = x[i:i + frame_size]
        frames.append(np.sqrt(np.mean(f * f)))
    if not frames:
        return np.array([])
    return np.array(frames)


def _find_zero_crossing(arr: np.ndarray, idx: int, search_radius: int = 64) -> int:
    start = max(0, idx - search_radius)
    end = min(len(arr) - 1, idx + search_radius)
    segment = arr[start:end]
    signs = np.sign(segment)
    zc = np.where(np.diff(signs) != 0)[0]
    if zc.size == 0:
        return idx
    return start + int(zc[0])


def extract_samples(stems: Dict[str, str], output_base: str, track_name: str, config: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Extract slices from repaired stems.

    Parameters:
        stems: mapping stem -> path
        output_base: base dir to write samples
        track_name: name of track
        config: options (thresholds, min/max lengths in ms, pads)

    Returns a list of metadata dicts for each slice or error objects.
    """
    cfg = config or {}
    silence_thresh = float(cfg.get('silence_threshold', 0.01))
    frame_size = int(cfg.get('frame_size', 1024))
    hop = int(cfg.get('hop', 512))
    transient_sensitivity = float(cfg.get('transient_sensitivity', 1.5))
    pre_ms = int(cfg.get('pre_ms', 20))
    post_ms = int(cfg.get('post_ms', 80))
    min_ms = int(cfg.get('min_slice_ms', 50))
    max_ms = int(cfg.get('max_slice_ms', 10000))

    logger.info('Extractor config: silence_thresh=%s frame_size=%s hop=%s transient_sensitivity=%s', silence_thresh, frame_size, hop, transient_sensitivity)

    out_samples_dir = os.path.join(output_base, track_name, 'samples')
    os.makedirs(out_samples_dir, exist_ok=True)

    results: List[Dict[str, Any]] = []

    all_slices = []

    for stem, path in stems.items():
        stem_dir = os.path.join(out_samples_dir, stem)
        os.makedirs(stem_dir, exist_ok=True)
        try:
            audio, sr = _read_wav(path)
            logger.info('Loaded stem=%s sr=%d len=%d', stem, sr, len(audio))

            # compute frame RMS and detect energy peaks
            rms = _frame_rms(audio, frame_size=frame_size, hop=hop)
            if rms.size == 0:
                logger.warning('No frames for stem %s', stem)
                continue
            mean = float(rms.mean())
            std = float(rms.std())
            thresh = mean + transient_sensitivity * std
            logger.info('Stem=%s rms mean=%.6f std=%.6f thresh=%.6f', stem, mean, std, thresh)

            # find transient frame indices (local maxima above threshold)
            transients = []
            for i in range(1, len(rms) - 1):
                if rms[i] > thresh and rms[i] > rms[i - 1] and rms[i] >= rms[i + 1]:
                    transients.append((i, float(rms[i])))

            logger.info('Detected %d transients for stem=%s', len(transients), stem)

            # Fallback: if no transients found with the configured frame size,
            # try a shorter-frame energy detector to catch very brief impulses
            if len(transients) == 0:
                logger.info('No transients detected with frame_size=%d, trying short-frame fallback', frame_size)
                short_fs = max(64, min(256, frame_size // 4))
                short_hop = max(32, short_fs // 2)
                short_rms = _frame_rms(audio, frame_size=short_fs, hop=short_hop)
                if short_rms.size > 0:
                    s_mean = float(short_rms.mean())
                    s_std = float(short_rms.std())
                    s_thresh = max(s_mean + 0.5 * s_std, 0.1 * float(short_rms.max()))
                    for i in range(len(short_rms)):
                        prev_val = short_rms[i - 1] if i > 0 else 0.0
                        next_val = short_rms[i + 1] if i < (len(short_rms) - 1) else 0.0
                        if short_rms[i] > s_thresh and short_rms[i] > prev_val and short_rms[i] >= next_val:
                            # map short-frame index back to main hop/frame grid approximately
                            mapped_idx = int((i * short_hop) / max(1, hop))
                            transients.append((mapped_idx, float(short_rms[i])))
                logger.info('Fallback detected %d transients for stem=%s', len(transients), stem)

            # convert frames to sample indices and create slices
            slices = []
            pre_samples = int(pre_ms * sr / 1000)
            post_samples = int(post_ms * sr / 1000)
            min_samples = int(min_ms * sr / 1000)
            max_samples = int(max_ms * sr / 1000)

            for idx, strength in transients:
                center_sample = idx * hop
                s0 = max(0, center_sample - pre_samples)
                s1 = min(len(audio), center_sample + post_samples)

                # expand to meet min length
                length = s1 - s0
                if length < min_samples:
                    extra = (min_samples - length) // 2
                    s0 = max(0, s0 - extra)
                    s1 = min(len(audio), s1 + extra)

                # enforce max
                if (s1 - s0) > max_samples:
                    s1 = s0 + max_samples

                # trim silence at both ends
                # compute local RMS around edges
                edge_frame = int(frame_size / 2)
                # trim start
                while s0 + edge_frame < s1:
                    seg = audio[s0:s0 + edge_frame]
                    if np.sqrt(np.mean(seg * seg)) < silence_thresh:
                        s0 += edge_frame
                    else:
                        break
                # trim end
                while s1 - edge_frame > s0:
                    seg = audio[s1 - edge_frame:s1]
                    if np.sqrt(np.mean(seg * seg)) < silence_thresh:
                        s1 -= edge_frame
                    else:
                        break

                # align to zero crossing
                s0_zc = _find_zero_crossing(audio, s0)
                s1_zc = _find_zero_crossing(audio, max(s0 + 1, s1 - 1))
                s0, s1 = max(0, s0_zc), min(len(audio), s1_zc)

                if s1 - s0 < min_samples:
                    logger.debug('Slice too short after trim/alignment, skipping')
                    continue

                slices.append({'start': s0, 'end': s1, 'strength': strength})

            # If no slices were produced via transient detection, try a naive
            # amplitude-based segmentation to catch very short impulses near
            # track boundaries (useful for edge-case tests).
            if len(slices) == 0:
                amp_thresh = max(silence_thresh * 10.0, 0.01)
                mask_idx = np.where(np.abs(audio) > amp_thresh)[0]
                if mask_idx.size > 0:
                    logger.info('Naive segmentation: found %d non-silent samples, generating slices', mask_idx.size)
                    # find contiguous runs
                    runs = []
                    run_start = mask_idx[0]
                    prev = mask_idx[0]
                    for idx in mask_idx[1:]:
                        if idx > prev + 1:
                            runs.append((run_start, prev))
                            run_start = idx
                        prev = idx
                    runs.append((run_start, prev))
                    for rs, re in runs:
                        s0 = max(0, rs - pre_samples)
                        s1 = min(len(audio), re + post_samples)
                        if s1 - s0 >= min_samples:
                            slices.append({'start': int(s0), 'end': int(s1), 'strength': float(np.max(np.abs(audio[rs:re+1])) )})
            logger.info('Stem=%s produced %d slices', stem, len(slices))

            # collect slices with absolute start times so we can deterministically order later
            for i, sl in enumerate(slices):
                s0, s1 = sl['start'], sl['end']
                meta = {'stem': stem, 'slice_index': i + 1, 'start_sample': int(s0), 'end_sample': int(s1), 'start_time': float(s0 / sr), 'end_time': float(s1 / sr), 'duration': float((s1 - s0) / sr), 'transient_strength': float(sl['strength']), 'audio': audio[s0:s1], 'sr': sr}
                all_slices.append(meta)
            logger.info('Stem=%s produced %d slices (collected)', stem, len(slices))

        except Exception as e:
            logger.exception('Error extracting from stem %s: %s', stem, e)
            results.append({'stem': stem, 'error': str(e)})

    # Deterministic ordering: sort by start_time then by stem name
    all_slices_sorted = sorted(all_slices, key=lambda m: (m['start_time'], m['stem']))

    # write out files with deterministic numbering and produce final metadata
    seq = 1
    for item in all_slices_sorted:
        stem = item['stem']
        stem_dir = os.path.join(out_samples_dir, stem)
        os.makedirs(stem_dir, exist_ok=True)
        fname = f"{track_name}_{stem}_{seq:04d}.wav"
        out_path = os.path.join(stem_dir, fname)
        _write_wav(out_path, item['audio'], item['sr'])
        meta = {'stem': stem, 'index': seq, 'start_sample': item['start_sample'], 'end_sample': item['end_sample'], 'start_time': item['start_time'], 'end_time': item['end_time'], 'duration': item['duration'], 'transient_strength': item['transient_strength'], 'path': os.path.abspath(out_path)}
        results.append(meta)
        logger.info('Wrote sample: %s meta=%s', out_path, meta)
        seq += 1

    # write manifest
    try:
        import json
        manifest = {'track': track_name, 'total_samples': len(results), 'samples': results}
        manifest_path = os.path.join(output_base, track_name, 'samples', 'samples_manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as mf:
            json.dump(manifest, mf, indent=2)
        logger.info('Wrote samples manifest: %s', manifest_path)
    except Exception:
        logger.exception('Failed to write samples manifest')

    return results
