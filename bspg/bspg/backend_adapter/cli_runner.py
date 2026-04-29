"""Subprocess runner stub for backend CLI adapter."""

import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional

from bspg.core.logging import bspg_logger
from pathlib import Path

# stage adapters
from bspg.backend_adapter.stage1_demucs import Stage1Demucs
from bspg.backend_adapter.stage2_repair import Stage2Repair
from bspg.backend_adapter.stage3_slicer import Stage3Slicer


def run_cli(args: List[str]):
    """Run backend CLI with provided args. This is a placeholder stub; real
    implementation will be added by later blocks.
    """
    try:
        completed = subprocess.run(args, capture_output=True, text=True)
        return completed.returncode, completed.stdout, completed.stderr
    except Exception as e:
        return 1, '', str(e)


@dataclass
class BackendCommand:
    args: List[str]
    description: str = ''


@dataclass
class BackendProcessResult:
    exit_code: int
    raw_output: List[str]
    raw_error: List[str]


class BackendRunner:
    def __init__(self, backend_path: Optional[str] = None):
        # backend_path can be a script or executable; left optional here
        self.backend_path = backend_path or 'backend_cli'
        self.logger = bspg_logger

    def build_command(self, config) -> List[str]:
        """Convert AppConfig into a CLI argument list.

        This is a deterministic, minimal implementation that composes the
        command from `config.paths` and `config.flowchart`. It does not
        perform validation.
        """
        args: List[str] = [self.backend_path]
        try:
            paths = getattr(config, 'paths', None)
            if paths and getattr(paths, 'input_files', None):
                for f in paths.input_files:
                    args.extend(['--input', f])
            out = getattr(paths, 'output_folder', None) if paths else None
            if out:
                args.extend(['--output', out])
        except Exception:
            pass
        # Chop settings
        try:
            chop = getattr(config, 'chop', None)
            if chop is not None:
                args.extend(['--silence-threshold', str(float(chop.silence_threshold))])
                args.extend(['--transient-sensitivity', str(float(chop.transient_sensitivity))])
        except Exception:
            pass
        return args

    def run_command(self, args: List[str]) -> BackendProcessResult:
        """Run the provided command synchronously and emit logs for output.

        This implementation captures stdout/stderr and emits each line via
        the BSPGLogger. It returns a BackendProcessResult.
        """
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate()
            out_lines = stdout.splitlines() if stdout else []
            err_lines = stderr.splitlines() if stderr else []
            # emit logs
            for line in out_lines:
                self.logger.info('backend', line)
            for line in err_lines:
                self.logger.error('backend', line)
            return BackendProcessResult(exit_code=proc.returncode or 0, raw_output=out_lines, raw_error=err_lines)
        except Exception as e:
            self.logger.error('backend', f'runner exception: {e}')
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=[str(e)])

    # --- Stage orchestration helpers ---
    def run_stage1(self, input_file: str, stage_out: str, model: str = 'htdemucs') -> int:
        demucs = Stage1Demucs()
        in_p = Path(input_file)
        out_p = Path(stage_out)
        try:
            rc = demucs.run(in_p, out_p, model=model)
            self.logger.info('stage1', f'completed {in_p} -> {out_p} rc={rc}')
            return rc
        except Exception as e:
            self.logger.error('stage1', f'error: {e}')
            return 1

    def run_stage2(self, input_file: str, out_file: str, options: list | None = None) -> int:
        repair = Stage2Repair()
        try:
            rc = repair.run(Path(input_file), Path(out_file), options=options)
            self.logger.info('stage2', f'completed {input_file} -> {out_file} rc={rc}')
            return rc
        except Exception as e:
            self.logger.error('stage2', f'error: {e}')
            return 1

    def run_stage3(self, input_file: str, out_folder: str, base_name: str = 'slice', count: int = 1) -> list:
        slicer = Stage3Slicer()
        try:
            outs = slicer.run(Path(input_file), Path(out_folder), base_name=base_name, count=count)
            for p in outs:
                self.logger.info('stage3', f'produced {p}')
            return outs
        except Exception as e:
            self.logger.error('stage3', f'error: {e}')
            return []

    def run_pipeline(self, config) -> BackendProcessResult:
        """Simple 3-stage pipeline runner that executes stages sequentially.

        This is intentionally minimal: it finds the first input file from
        `config.paths.input_files` and writes outputs under
        `config.paths.output_folder` in `stage1/`, `stage2/`, `stage3/`.
        """
        paths = getattr(config, 'paths', None)
        if not paths or not getattr(paths, 'input_files', None):
            self.logger.error('pipeline', 'no input files')
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=['no input files'])

        input_file = Path(paths.input_files[0])
        base_out = Path(getattr(paths, 'output_folder', '.'))
        stage1_out = base_out / 'stage1'
        stage2_out = base_out / 'stage2'
        stage3_out = base_out / 'stage3'
        stage1_out.mkdir(parents=True, exist_ok=True)
        stage2_out.mkdir(parents=True, exist_ok=True)
        stage3_out.mkdir(parents=True, exist_ok=True)

        rc1 = self.run_stage1(str(input_file), str(stage1_out))
        if rc1 != 0:
            return BackendProcessResult(exit_code=rc1, raw_output=[], raw_error=['stage1 failed'])

        # For placeholder flow, pick first file in stage1_out as input to stage2
        stage1_files = list(stage1_out.iterdir())
        if not stage1_files:
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=['no files from stage1'])
        stage2_in = stage1_files[0]
        stage2_out_file = stage2_out / f'repaired{stage2_in.suffix}'
        rc2 = self.run_stage2(str(stage2_in), str(stage2_out_file))
        if rc2 != 0:
            return BackendProcessResult(exit_code=rc2, raw_output=[], raw_error=['stage2 failed'])

        outs = self.run_stage3(str(stage2_out_file), str(stage3_out), base_name='slice', count=1)
        if not outs:
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=['stage3 failed'])

        return BackendProcessResult(exit_code=0, raw_output=[str(p) for p in outs], raw_error=[])
