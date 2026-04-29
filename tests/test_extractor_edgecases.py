import os
import wave
import numpy as np
import tempfile
from hqspg.extractor import extract_samples


def write_wav(path, data, sr=44100):
    int16 = (np.clip(data, -1.0, 1.0) * np.iinfo(np.int16).max).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16.tobytes())


def test_short_slices_and_silence_only(tmp_path):
    sr = 44100
    # create a short audio with silence-only
    silence = np.zeros(sr // 2, dtype=np.float32)
    long_silence_path = tmp_path / 'silence.wav'
    write_wav(str(long_silence_path), silence, sr)

    results = extract_samples({'vocals': str(long_silence_path)}, str(tmp_path), 'testtrack', config={'min_slice_ms': 10})
    # should return empty list or not crash
    assert isinstance(results, list)


def test_boundary_alignment(tmp_path):
    sr = 44100
    # create a signal with a transient near the start and end
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = np.zeros_like(t)
    # impulse near start
    audio[10:20] = 1.0
    # impulse near end
    audio[-30:-20] = 1.0
    path = tmp_path / 'impulses.wav'
    write_wav(str(path), audio, sr)

    results = extract_samples({'drums': str(path)}, str(tmp_path), 'boundary', config={'pre_ms': 5, 'post_ms': 5, 'min_slice_ms': 5})
    # expect at least two slices
    assert isinstance(results, list)
    assert len(results) >= 2
    # ensure slices have nonzero duration
    for r in results:
        assert r.get('duration', 0) > 0
