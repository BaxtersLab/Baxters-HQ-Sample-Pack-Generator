import subprocess
import logging
from pathlib import Path


class Stage2Repair:
    """Placeholder wrapper for a repair/generative stage.

    By default this will attempt to run a configurable CLI tool; it's
    implemented so tests can monkeypatch the subprocess invocation.
    """

    def __init__(self, repair_exe: str = "repair_tool"):
        self.repair_exe = repair_exe
        self.logger = logging.getLogger(__name__)

    def build_command(self, input_file: Path, out_file: Path, options: list[str] | None = None):
        cmd = [self.repair_exe, str(input_file), str(out_file)]
        if options:
            cmd.extend(options)
        return cmd

    def run(self, input_file: Path, out_file: Path, options: list[str] | None = None, timeout: float | None = None):
        cmd = self.build_command(input_file, out_file, options=options)
        self.logger.info("Starting Repair: %s", " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if proc.stdout is not None:
            for line in proc.stdout:
                self.logger.info(line.rstrip())
        rc = proc.wait(timeout=timeout)
        if rc != 0:
            raise RuntimeError(f"Repair stage failed with code {rc}")
        return rc
