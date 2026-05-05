"""Backend output parser for converting raw CLI lines into structured events."""

import re
import time
from typing import Optional

from bspg.core.logging import bspg_logger
from bspg.backend_adapter.pipeline_state import PipelineEvent, PipelineState, PipelineStage
from bspg.core.errors import BackendError


class BackendOutputParser:
    def __init__(self):
        self.state = PipelineState()
        self.logger = bspg_logger

    def detect_stage(self, line: str) -> Optional[str]:
        l = line.lower()
        if 'stem' in l and 'separat' in l:
            return PipelineStage.STEM_SEPARATION
        if 'repair' in l:
            return PipelineStage.STEM_REPAIR
        if 'chop' in l or 'chopping' in l:
            return PipelineStage.SAMPLE_CHOP
        if 'finaliz' in l:
            return PipelineStage.FINALIZING
        if 'complete' in l or 'pipeline complete' in l:
            return PipelineStage.COMPLETE
        return None

    def detect_progress(self, line: str) -> Optional[float]:
        # look for patterns like 'Progress: 42%' or '42% complete'
        m = re.search(r"(\d{1,3})\s*%", line)
        if m:
            try:
                v = int(m.group(1))
                return max(0.0, min(1.0, v / 100.0))
            except Exception:
                return None
        return None

    def detect_error(self, line: str) -> Optional[BackendError]:
        l = line.lower()
        if 'error' in l or 'failed' in l or 'exception' in l:
            return BackendError(message=line)
        return None

    def parse_line(self, line: str) -> PipelineEvent:
        ts = time.time()
        stage = self.detect_stage(line) or self.state.stage
        err = self.detect_error(line)
        level = 'ERROR' if err else 'INFO'
        evt = PipelineEvent(timestamp=ts, stage=stage, message=line.strip(), raw_line=line, level=level)
        # append to state
        self.state.events.append(evt)
        # emit structured log
        if err:
            self.logger.error('backend', line.strip())
        else:
            self.logger.info('backend', line.strip())
        return evt

    def update_state(self, event: PipelineEvent) -> PipelineState:
        # update stage
        if event.stage:
            self.state.stage = event.stage
        # update progress if present
        prog = self.detect_progress(event.raw_line)
        if prog is not None:
            self.state.progress = prog
        # detect errors
        err = self.detect_error(event.raw_line)
        if err:
            self.state.error = err
            self.state.stage = PipelineStage.ERROR
        return self.state

    def finalize(self, exit_code: int) -> PipelineState:
        self.state.exit_code = exit_code
        if exit_code == 0:
            self.state.stage = PipelineStage.COMPLETE
            self.state.progress = 1.0
        else:
            self.state.stage = PipelineStage.ERROR
        return self.state


def parse_cli_output(stdout: str):
    # backward-compatible helper: split stdout into lines and parse
    p = BackendOutputParser()
    for line in (stdout or '').splitlines():
        evt = p.parse_line(line)
        p.update_state(evt)
    return p.state
