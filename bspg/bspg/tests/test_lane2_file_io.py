from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.top_lanes.lane2_file_io import TopLaneFileIO


def test_lane2_instantiation():
    app = QApplication.instance() or QApplication(sys.argv)
    w = TopLaneFileIO()
    assert w.input_button is not None
    assert w.output_button is not None
    assert w.thermometer_label is not None
    assert w.hrt_beacon_label is not None
    w.close()
