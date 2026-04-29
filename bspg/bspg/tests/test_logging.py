from bspg.core.logging import LogLevel, LogMessage, DebugSink, LogRouter, BSPGLogger


class DummySink(DebugSink):
    def __init__(self):
        self.messages = []

    def emit(self, log: LogMessage) -> None:
        self.messages.append(log)


def test_logging_router_and_sink():
    router = LogRouter()
    sink = DummySink()
    router.add_sink(sink)
    router.log(LogLevel.INFO, 'backend', 'ok')
    assert len(sink.messages) == 1
    assert sink.messages[0].level == LogLevel.INFO

    router.remove_sink(sink)
    router.log(LogLevel.DEBUG, 'backend', 'ignored')
    assert len(sink.messages) == 1

    bl = BSPGLogger(router)
    # adding sink back
    router.add_sink(sink)
    bl.error('flowchart', 'bad')
    assert sink.messages[-1].level == LogLevel.ERROR
