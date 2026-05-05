from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.main_window import MainWindow


def test_main_window_instantiation(qtbot=None):
    app = QApplication.instance() or QApplication(sys.argv)
    w = MainWindow()
    assert w.top_lane_container is not None
    assert w.logo_container is not None
    assert w.flowchart_container is not None
    assert w.debug_terminal_container is not None
    w.close()
