from typing import Any

from bspg.core.logging import DebugSink, LogMessage


class DebugTerminalSinkAdapter(DebugSink):
    """Adapter that forwards LogMessage instances to an existing
    debug-terminal-like object exposing `append_log(str)`.

    This class is additive and non-invasive; it performs a best-effort
    forward and never raises.
    """

    def __init__(self, terminal: Any):
        self.terminal = terminal

    def emit(self, log: LogMessage) -> None:
        try:
            line = f"[{log.level}] {log.source}: {log.message}"
            if hasattr(self.terminal, 'append_log'):
                # append_log is thread-safe (routes via queue+timer)
                self.terminal.append_log(line)
            else:
                # Fallback for plain QTextEdit — avoid direct cross-thread call.
                # append_log not available so we silently drop rather than risk a crash.
                pass
        except Exception:
            return
