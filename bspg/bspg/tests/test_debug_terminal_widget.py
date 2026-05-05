from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.debug_terminal.debug_terminal_widget import DebugTerminalWidget
from bspg.core.logging import bspg_logger


def test_debug_terminal_receives_logs():
    app = QApplication.instance() or QApplication(sys.argv)
    widget = DebugTerminalWidget()
    # emit a log via the global logger
    bspg_logger.info('test', 'hello debug')
    # the sink appends asynchronously within same thread, assert text exists
    content = widget.text_area.toPlainText()
    assert 'hello debug' in content
    widget.clear()
    widget.close()
