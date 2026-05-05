import subprocess
import sys
import logging
from pathlib import Path


class Stage1Demucs:
    """Wrapper around a Demucs CLI invocation for stem extraction.

    This is intentionally lightweight: it builds a command list and streams
    stdout/stderr lines to the logger so the GUI/backend parser can consume
    progress messages.
    """

    def __init__(self, demucs_exe: str = "demucs"):
        self.demucs_exe = demucs_exe
        self.logger = logging.getLogger(__name__)

    # Path to the soundfile-patching runner (sits alongside this file)
    _RUNNER = Path(__file__).parent / "_demucs_runner.py"

    def build_command(self, input_file: Path, out_dir: Path, model: str = "htdemucs"):
        out_dir = Path(out_dir)
        # Use the thin wrapper that patches torchaudio.save → soundfile before
        # demucs loads.  Falls back to a bare exe path only if the user has
        # overridden demucs_exe to something custom.
        if self.demucs_exe == "demucs":
            exe_args = [sys.executable, str(self._RUNNER)]
        else:
            exe_args = [self.demucs_exe]
        return exe_args + ["-n", model, "-o", str(out_dir), str(input_file)]

    def run(self, input_file: Path, out_dir: Path, model: str = "htdemucs", timeout: float | None = None):
        cmd = self.build_command(input_file, out_dir, model=model)
        self.logger.info("Starting Demucs: %s", " ".join(cmd))
        # stderr is NOT merged — tqdm writes carriage-return progress lines to
        # stderr and merging them into the stdout pipe causes broken-pipe / early
        # exit issues.  Let stderr pass through to the console unfiltered.
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout — no black window
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if __import__('sys').platform == 'win32' else 0,
        )
        if proc.stdout is not None:
            for line in proc.stdout:
                self.logger.info(line.rstrip())
        rc = proc.wait(timeout=timeout)
        return rc
