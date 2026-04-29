import subprocess
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

    def build_command(self, input_file: Path, out_dir: Path, model: str = "htdemucs"):
        out_dir = Path(out_dir)
        return [self.demucs_exe, "-n", model, "-o", str(out_dir), str(input_file)]

    def run(self, input_file: Path, out_dir: Path, model: str = "htdemucs", timeout: float | None = None):
        cmd = self.build_command(input_file, out_dir, model=model)
        self.logger.info("Starting Demucs: %s", " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Stream lines to logger
        if proc.stdout is not None:
            for line in proc.stdout:
                self.logger.info(line.rstrip())
        rc = proc.wait(timeout=timeout)
        if rc != 0:
            raise RuntimeError(f"Demucs failed with code {rc}")
        return rc
