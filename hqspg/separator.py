"""HQSPG separator module.

Implements a simple wrapper around the Demucs CLI. This module runs
Demucs as a subprocess (preferring an installed `demucs` command and
falling back to `python -m demucs`) and returns a mapping of stem name
to absolute WAV path. Errors are returned as structured dicts.
"""
from typing import Dict, Optional, Any
import logging
import os
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


class HQSeparator:
  """Separator wrapper for Demucs.

  Usage:
    separator = HQSeparator(model='htdemucs_6s')
    mapping = separator.separate('/path/to/track.wav', output_base='/out/base')

  The method writes stems to: <output_base>/<track_name>/stems/
  and returns a dict mapping stem_name -> absolute path.
  """

  def __init__(self, model: str = 'htdemucs_6s', config: Optional[Dict] = None, logger_obj: Optional[logging.Logger] = None):
    self.model = model
    self.config = config or {}
    self.logger = logger_obj or logger
    self.logger.debug('HQSeparator initialized model=%s config=%s', model, self.config)

  def _detect_gpu(self) -> bool:
    """Return True if a CUDA GPU appears available (best-effort).

    We try importing torch and calling torch.cuda.is_available(). If
    torch is not installed, assume CPU and log that.
    """
    try:
      import torch

      avail = torch.cuda.is_available()
      self.logger.debug('torch detected, cuda available=%s', avail)
      return bool(avail)
    except Exception:
      self.logger.debug('torch not available; assuming CPU mode')
      return False

  def _find_demucs_executable(self) -> Optional[str]:
    """Return the demucs executable command to run or None if not found.

    Preference order:
    1. `demucs` on PATH
    2. `python -m demucs` via current interpreter
    """
    cmd = shutil.which('demucs')
    if cmd:
      return cmd
    # fallback to running module via python
    # ensure the demucs package is importable; we'll still attempt to run and capture errors
    return None

  def separate(self, input_file: str, output_base: Optional[str] = None) -> Dict[str, Any]:
    """Run Demucs separation for `input_file`.

    Parameters:
      input_file: path to the audio file
      output_base: root output directory (will create <output_base>/<track>/stems/)

    Returns:
      dict mapping stem name -> absolute path on success, or a dict
      containing an 'error' key with diagnostic information on failure.
    """
    if not os.path.isfile(input_file):
      msg = f'Input file not found: {input_file}'
      self.logger.error(msg)
      return {'error': msg}

    track_name = os.path.splitext(os.path.basename(input_file))[0]
    out_base = output_base or self.config.get('output_base') or os.path.join(os.path.dirname(input_file), 'demucs_out')
    # target stems directory per requirement
    stems_dir = os.path.join(out_base, track_name, 'stems')
    os.makedirs(stems_dir, exist_ok=True)

    gpu = self._detect_gpu()
    self.logger.info('Separating %s using model=%s (gpu=%s)', input_file, self.model, gpu)

    demucs_cmd = shutil.which('demucs')
    if demucs_cmd:
      cmd = [demucs_cmd, '-n', self.model, '-o', out_base, input_file]
    else:
      # use python -m demucs fallback
      cmd = [sys.executable, '-m', 'demucs', '-n', self.model, '-o', out_base, input_file]

    self.logger.info('Running demucs command: %s', ' '.join(cmd))

    try:
      proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as e:
      msg = f'Failed to execute Demucs: {e}'
      self.logger.error(msg)
      return {'error': msg, 'exception': str(e)}

    if proc.returncode != 0:
      # Demucs failed; return stdout/stderr for diagnosis
      msg = f'Demucs exited with code {proc.returncode}'
      self.logger.error('%s\nstdout: %s\nstderr: %s', msg, proc.stdout, proc.stderr)
      return {'error': msg, 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}

    # On success, scan stems_dir for wav files and build mapping
    expected_dir = stems_dir
    if not os.path.isdir(expected_dir):
      # demucs may have used a different structure; attempt to locate
      candidate = os.path.join(out_base, track_name, 'stems')
      if os.path.isdir(candidate):
        expected_dir = candidate

    if not os.path.isdir(expected_dir):
      # try to find a directory under out_base that contains the track_name
      found = None
      for root, dirs, files in os.walk(out_base):
        if os.path.basename(root) == 'stems' and track_name in root:
          found = root
          break
      if found:
        expected_dir = found

    if not os.path.isdir(expected_dir):
      msg = f'Could not locate stems directory after Demucs run under {out_base}'
      self.logger.error(msg)
      return {'error': msg, 'stdout': proc.stdout, 'stderr': proc.stderr}

    mapping: Dict[str, str] = {}
    for fname in sorted(os.listdir(expected_dir)):
      if not fname.lower().endswith('.wav'):
        continue
      # attempt to derive stem name from filename
      # common demucs pattern: <track>_<stem>.wav
      if fname.startswith(track_name + '_'):
        stem = fname[len(track_name) + 1:]
      else:
        stem = os.path.splitext(fname)[0]
      stem = os.path.splitext(stem)[0]
      abs_path = os.path.abspath(os.path.join(expected_dir, fname))
      mapping[stem] = abs_path
      self.logger.info('Found stem: %s -> %s', stem, abs_path)

    return mapping


def separate(file: str, out_dir: Optional[str] = None, model: Optional[str] = None, config: Optional[Dict] = None) -> Dict[str, Any]:
  """Wrapper for GUI/controller: runs separation and returns mapping."""
  sep = HQSeparator(model=model or (config or {}).get('model', 'htdemucs_6s'), config=config or {})
  return sep.separate(file, output_base=out_dir)
