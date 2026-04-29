"""HQSPG repair module.

Implements simple glimmer detection and two repair modes:
- `fast`: time-domain smoothing (lower latency)
- `balanced`: STFT-based magnitude interpolation (higher quality)

This implementation is intentionally lightweight and avoids heavy
external dependencies where possible. It logs per-stem stats and
returns structured results or errors.
"""
from typing import Dict, Optional, Any
import logging
import os
import wave
import numpy as np

try:
    from scipy.signal import medfilt
except Exception:
    medfilt = None

logger = logging.getLogger(__name__)


def _read_wav(path: str):
    with wave.open(path, 'rb') as wf:
        nchan = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fr = wf.getframerate()
        nframes = wf.getnframes()
        data = wf.readframes(nframes)
    # support 16-bit PCM
    if sampwidth == 2:
        dtype = np.int16
    else:
        # fallback: interpret as bytes
        dtype = np.int16
    audio = np.frombuffer(data, dtype=dtype).astype(np.float32)
    if nchan > 1:
        audio = audio.reshape(-1, nchan).mean(axis=1)
    # normalize to [-1,1]
    audio = audio / (np.iinfo(np.int16).max if dtype == np.int16 else 1.0)
    return audio, fr


def _write_wav(path: str, audio: np.ndarray, sr: int):
    # convert float[-1,1] to int16
    clipped = np.clip(audio, -1.0, 1.0)
    int16 = (clipped * np.iinfo(np.int16).max).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16.tobytes())


def _frame_rms(x: np.ndarray, frame_size: int = 2048, hop: int = 512):
    frames = []
    for i in range(0, max(1, len(x) - frame_size + 1), hop):
        f = x[i:i + frame_size]
        frames.append(np.sqrt(np.mean(f * f)))
    if not frames:
        return np.array([])
    return np.array(frames)


class HQRepair:
    def __init__(self, mode: str = 'balanced', config: Optional[Dict] = None, logger_obj: Optional[logging.Logger] = None):
        self.mode = mode
        self.config = config or {}
        self.logger = logger_obj or logger
        self.logger.debug('HQRepair initialized mode=%s config=%s', mode, self.config)

    def _detect_glimmer_regions(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        # compute frame RMS and mark outliers
        frame_size = int(self.config.get('frame_size', 2048))
        hop = int(self.config.get('hop', 512))
        rms = _frame_rms(audio, frame_size=frame_size, hop=hop)
        if rms.size == 0:
            return {'frames': [], 'stats': {'mean': 0.0, 'std': 0.0, 'count': 0}}
        mean = float(rms.mean())
        std = float(rms.std())
        sensitivity = float(self.config.get('glimmer_sensitivity', 0.02))
        threshold = mean + sensitivity * std
        flagged = np.where(rms > threshold)[0].tolist()
        stats = {'mean': mean, 'std': std, 'threshold': threshold, 'frames_total': int(len(rms)), 'flagged_count': int(len(flagged))}
        return {'frames': flagged, 'stats': stats}

    def _fast_repair(self, audio: np.ndarray) -> np.ndarray:
        # time-domain median/mean smoothing
        k = int(self.config.get('median_size', 7))
        if medfilt is not None:
            try:
                # medfilt requires odd kernel
                if k % 2 == 0:
                    k += 1
                repaired = medfilt(audio, kernel_size=k)
                return repaired.astype(np.float32)
            except Exception:
                pass
        # fallback: simple moving average
        if k <= 1:
            return audio
        kernel = np.ones(k) / k
        repaired = np.convolve(audio, kernel, mode='same')
        return repaired.astype(np.float32)

    def _balanced_repair(self, audio: np.ndarray, sr: int) -> np.ndarray:
        # simple STFT magnitude smoothing across flagged frames
        n_fft = int(self.config.get('n_fft', 2048))
        hop = int(self.config.get('hop', 512))
        win = np.hanning(n_fft)
        # pad signal
        pad = np.zeros(n_fft)
        sig = np.concatenate([audio, pad])
        # number of frames
        frames = 1 + (len(sig) - n_fft) // hop
        S = np.empty((n_fft // 2 + 1, frames), dtype=np.complex64)
        for i in range(frames):
            start = i * hop
            frame = sig[start:start + n_fft] * win
            spec = np.fft.rfft(frame)
            S[:, i] = spec

        mag = np.abs(S)
        phase = np.angle(S)

        # detect glimmer frames using RMS on the time-domain (coarse)
        regions = self._detect_glimmer_regions(audio, sr)
        flagged = regions.get('frames', [])

        # for flagged frames, replace magnitude with median across neighbors
        for f in flagged:
            lo = max(0, f - 2)
            hi = min(frames - 1, f + 2)
            # median across time for each freq bin
            median_mag = np.median(mag[:, lo:hi + 1], axis=1)
            mag[:, f] = median_mag

        # reconstruct
        S_recon = mag * np.exp(1j * phase)
        out = np.zeros(n_fft + hop * (frames - 1), dtype=np.float32)
        for i in range(frames):
            start = i * hop
            frame = np.fft.irfft(S_recon[:, i]) * win
            out[start:start + n_fft] += frame.real

        # trim to original length
        out = out[:len(audio)]
        return out

    def repair(self, stems: Dict[str, str], output_base: Optional[str] = None, track_name: Optional[str] = None) -> Dict[str, Any]:
        """Repair stems.

        Parameters:
            stems: dict mapping stem name -> path
            output_base: base directory to write repaired files
            track_name: optional track name used to create output path

        Returns a dict mapping stem name -> {'repaired_path':..., 'metadata':...} or error info.
        """
        results: Dict[str, Any] = {}
        mode = (self.mode or self.config.get('mode', 'balanced')).lower()
        self.logger.info('HQRepair starting mode=%s', mode)

        out_base = output_base or self.config.get('output_base') or os.getcwd()
        if track_name is None:
            track_name = 'repaired'
        target_dir = os.path.join(out_base, track_name, 'repaired')
        os.makedirs(target_dir, exist_ok=True)

        for stem_name, path in stems.items():
            self.logger.info('Processing stem=%s path=%s', stem_name, path)
            if not os.path.isfile(path):
                msg = f'stem file missing: {path}'
                self.logger.warning(msg)
                results[stem_name] = {'error': msg}
                continue
            try:
                audio, sr = _read_wav(path)
                detect = self._detect_glimmer_regions(audio, sr)
                self.logger.info('Glimmer stats for %s: %s', stem_name, detect.get('stats'))

                if mode == 'fast':
                    repaired = self._fast_repair(audio)
                    action = 'median_smoothing' if medfilt is not None else 'moving_average'
                else:
                    repaired = self._balanced_repair(audio, sr)
                    action = 'stft_median_interp'

                out_path = os.path.join(target_dir, f"{stem_name}_repaired.wav")
                _write_wav(out_path, repaired, sr)
                results[stem_name] = {'repaired_path': os.path.abspath(out_path), 'metadata': {'mode': mode, 'action': action, 'glimmer_stats': detect.get('stats')}}
                self.logger.info('Wrote repaired stem: %s', out_path)
            except Exception as e:
                self.logger.exception('Error repairing stem %s: %s', stem_name, e)
                results[stem_name] = {'error': str(e)}

        return results


def repair_stems(stems: Dict[str, str], output_base: Optional[str] = None, track_name: Optional[str] = None, config: Optional[Dict] = None) -> Dict[str, Any]:
    """Compatibility wrapper for GUI/controller."""
    rep = HQRepair(mode=(config or {}).get('mode', 'balanced'), config=config or {})
    return rep.repair(stems, output_base=output_base, track_name=track_name)
