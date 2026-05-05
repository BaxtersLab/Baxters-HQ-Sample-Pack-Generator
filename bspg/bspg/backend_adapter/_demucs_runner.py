"""Wrapper that patches torchaudio.save to use soundfile before demucs loads.

torchaudio 2.11+ removed the legacy soundfile backend in favour of torchcodec,
which ships without Windows DLLs on Python 3.14 / PyTorch CPU builds. This
script monkey-patches torchaudio.save with a soundfile implementation, then
delegates to demucs normally. All CLI args pass through unchanged.
"""
import sys
import torch
import soundfile as sf
import torchaudio


def _soundfile_save(path, src, sample_rate, channels_first=True, **_kwargs):
    """soundfile-based replacement for torchaudio.save."""
    wav = src.numpy() if isinstance(src, torch.Tensor) else src
    if channels_first and wav.ndim > 1:
        wav = wav.T  # soundfile expects (frames, channels)
    sf.write(str(path), wav, sample_rate)


torchaudio.save = _soundfile_save

from demucs.separate import main  # noqa: E402
sys.exit(main())
