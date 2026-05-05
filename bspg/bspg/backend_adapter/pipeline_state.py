"""Pipeline state model definitions."""
from dataclasses import dataclass, field
from typing import List, Optional
import time

from bspg.core.errors import BackendError


class PipelineStage:
    IDLE = 'IDLE'
    STEM_SEPARATION = 'STEM_SEPARATION'
    STEM_REPAIR = 'STEM_REPAIR'
    SAMPLE_CHOP = 'SAMPLE_CHOP'
    FINALIZING = 'FINALIZING'
    COMPLETE = 'COMPLETE'
    ERROR = 'ERROR'


@dataclass
class PipelineEvent:
    timestamp: float
    stage: str
    message: str
    raw_line: str
    level: str = 'INFO'


@dataclass
class PipelineState:
    stage: str = PipelineStage.IDLE
    progress: float = 0.0
    events: List[PipelineEvent] = field(default_factory=list)
    exit_code: Optional[int] = None
    error: Optional[BackendError] = None


@dataclass
class PipelineStatus:
    running: bool = False
    stage: str = PipelineStage.IDLE
    progress: float = 0.0
    error_message: Optional[str] = None
