from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.top_lanes.lane1_run_status import TopLaneRunStatus


def test_lane1_instantiation():
    app = QApplication.instance() or QApplication(sys.argv)
    w = TopLaneRunStatus()
    assert w.run_button is not None
    assert w.status_label is not None
    assert w.settings_button is not None
    assert w.debug_button is not None
    w.close()
