from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout

from bspg.core.logging import DebugSink, LogMessage, bspg_logger


class DebugTerminalWidget(QWidget):
    def __init__(self, logger: "bspg_logger" = None, parent=None):
        super().__init__(parent)
        self.logger = logger or bspg_logger
        self.initialized = False
        self.sink_registered = False
        self.init_ui()
        self.register_sink()

    def init_ui(self):
        if getattr(self, 'initialized', False):
            return
        self.initialized = True

        if not hasattr(self, 'text_area'):
            self.text_area = QTextEdit(self)
            self.text_area.setReadOnly(True)
            layout = QVBoxLayout(self)
            layout.addWidget(self.text_area)
            self.setLayout(layout)

    def register_sink(self):
        if getattr(self, 'sink_registered', False):
            return
        self.sink_registered = True

        class _Sink(DebugSink):
            def __init__(self, outer):
                self.outer = outer

            def emit(self, log: LogMessage) -> None:
                try:
                    self.outer.append_log(log)
                except Exception:
                    # avoid raising from sink
                    return

        self.sink = _Sink(self)
        self.logger.router.add_sink(self.sink)

    def append_log(self, log: LogMessage):
        line = f"[{log.level}] {log.source}: {log.message}"
        if hasattr(self, 'text_area'):
            self.text_area.append(line)

    def clear(self):
        if hasattr(self, 'text_area'):
            self.text_area.clear()

    def apply_styles(self):
        # placeholder for styling; must not alter existing QSS
        return


def integrate_with_existing(debug_terminal):
    """Integrate BSPG LogRouter with an existing DebugTerminal-like object.

    This is additive and non-invasive: it registers a DebugSink that forwards
    `LogMessage` instances to the provided `debug_terminal.append_log` method.
    """
    try:
        if debug_terminal is None:
            return

        class _ExtSink(DebugSink):
            def __init__(self, terminal):
                self.terminal = terminal

            def emit(self, log: LogMessage) -> None:
                try:
                    # format similarly to internal append_log
                    line = f"[{log.level}] {log.source}: {log.message}"
                    if hasattr(self.terminal, 'append_log'):
                        self.terminal.append_log(line)
                    else:
                        # fallback: try to append raw text if it's a QTextEdit
                        try:
                            self.terminal.append(line)
                        except Exception:
                            pass
                except Exception:
                    return

        sink = _ExtSink(debug_terminal)
        from bspg.core.logging import router

        router.add_sink(sink)
    except Exception:
        # integration is best-effort and must not raise
        return
