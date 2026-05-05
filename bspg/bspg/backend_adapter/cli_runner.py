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

    def run_pipeline(self, config, progress_callback=None) -> BackendProcessResult:
        """Run the full hqspg pipeline (separate → repair → extract) by calling
        hqspg.cli.run_pipeline_for_file directly.

        `progress_callback(msg: str)` is forwarded to run_pipeline_for_file so
        the GUI receives live stage-boundary updates.
        """
        from hqspg.cli import run_pipeline_for_file

        paths = getattr(config, 'paths', None)
        if not paths or not getattr(paths, 'input_files', None):
            self.logger.error('pipeline', 'no input files')
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=['no input files'])

        input_file = str(Path(paths.input_files[0]))
        base_out   = str(Path(getattr(paths, 'output_folder', '.')))

        # Build config dict from AppConfig fields
        chop = getattr(config, 'chop', None)
        extractor_cfg = {
            'silence_threshold':    float(getattr(chop, 'silence_threshold',    0.01)),
            'transient_sensitivity': float(getattr(chop, 'transient_sensitivity', 1.5)),
            'pre_ms':               int(getattr(chop,   'pre_ms',               20)),
            'post_ms':              int(getattr(chop,   'post_ms',              80)),
            'min_slice_ms':         int(getattr(chop,   'min_slice_ms',         50)),
            'max_slice_ms':         int(getattr(chop,   'max_slice_ms',         10000)),
        }

        cfg_dict = {
            'separator': {'model': 'htdemucs_6s'},
            'repair':    {'mode': 'balanced'},
            'extractor': extractor_cfg,
        }

        self.logger.info('pipeline', f'Starting pipeline: {input_file} -> {base_out}')
        self.logger.info('pipeline', f'Extractor config: {extractor_cfg}')

        # ── Determine routing from flowchart config ──────────────────────────
        # Explicit gate patterns take PRIORITY over cb8.
        # cb8 is the "full auto" fallback — it only fires when no specific
        # pattern matches, so individual gate configs always win.
        fc = getattr(config, 'flowchart', None)
        if fc is not None:
            cb1 = bool(getattr(fc, 'cb1', False))
            cb2 = bool(getattr(fc, 'cb2', False))
            cb3 = bool(getattr(fc, 'cb3', False))
            cb4 = bool(getattr(fc, 'cb4', False))
            cb5 = bool(getattr(fc, 'cb5', False))
            cb6 = bool(getattr(fc, 'cb6', False))
            cb7 = bool(getattr(fc, 'cb7', False))
            cb8 = bool(getattr(fc, 'cb8', False))
        else:
            cb1 = cb2 = cb3 = cb4 = cb5 = cb6 = cb7 = cb8 = False

        if cb1 and not cb2 and not cb4 and not cb5 and not cb7:
            stages = 'sep_only'             # cb1 only — Demucs, output stems, stop
        elif cb2 and cb3 and not cb5:
            stages = 'sep_repair'           # sep → repair, no chop (cb1 optional)
        elif cb7 and cb6 and not cb2:
            stages = 'byo_chop'             # BYO → chop directly
        elif cb4 and cb5 and cb6 and not cb2:
            stages = 'byo_repair_chop'      # BYO → repair → chop
        else:
            stages = 'full'                 # full pipeline (cb8, all gates, or fallback)

        self.logger.info('pipeline', f'Flowchart routing: stages={stages} '
                         f'(cb1={cb1} cb2={cb2} cb3={cb3} cb4={cb4} '
                         f'cb5={cb5} cb6={cb6} cb7={cb7} cb8={cb8})')

        try:
            result = run_pipeline_for_file(input_file, cfg_dict, base_out, progress_callback=progress_callback, stages=stages)
        except Exception as e:
            self.logger.error('pipeline', f'Pipeline exception: {e}')
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=[str(e)])

        if result.get('error'):
            self.logger.error('pipeline', f"Pipeline error: {result['error']}")
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=[result['error']])

        slices = result.get('slices', [])
        if isinstance(slices, dict) and slices.get('error'):
            self.logger.error('pipeline', f"Extractor error: {slices['error']}")
            return BackendProcessResult(exit_code=1, raw_output=[], raw_error=[slices['error']])

        out_paths = [s['path'] for s in slices if isinstance(s, dict) and s.get('path')]
        total = len(out_paths)
        self.logger.info('pipeline', f'Pipeline finished with errors: exit=0 slices={total}')
        return BackendProcessResult(exit_code=0, raw_output=out_paths, raw_error=[])

