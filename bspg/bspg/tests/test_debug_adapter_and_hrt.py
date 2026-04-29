from bspg.gui.debug_terminal.adapter import DebugTerminalSinkAdapter
from bspg.core.logging import LogMessage


class FakeTerminal:
    def __init__(self):
        self.lines = []

    def append_log(self, line: str):
        self.lines.append(line)


def test_debug_terminal_adapter_forwards_message():
    t = FakeTerminal()
    adapter = DebugTerminalSinkAdapter(t)
    log = LogMessage(level='INFO', source='unit', message='hello')
    adapter.emit(log)
    assert len(t.lines) == 1
    assert 'hello' in t.lines[0]


from bspg.gui.hrt.hrt_connector import HRTConnector


def test_hrt_connector_callbacks():
    c = HRTConnector()
    calls = []

    def on_connect():
        calls.append('connect')

    def on_disconnect():
        calls.append('disconnect')

    c.set_callback('on_connect', on_connect)
    c.set_callback('on_disconnect', on_disconnect)
    c.connect()
    assert c.is_connected() is True
    assert 'connect' in calls
    c.disconnect()
    assert c.is_connected() is False
    assert 'disconnect' in calls
