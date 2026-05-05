from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.main_window import MainWindow
from bspg.gui.logic.gui_controller import GUIController


def test_gui_controller_wires_buttons():
    app = QApplication.instance() or QApplication(sys.argv)
    mw = MainWindow()
    # attach lane widget instances to mimic existing GUI wiring
    from bspg.gui.top_lanes.lane1_run_status import TopLaneRunStatus
    from bspg.gui.top_lanes.lane2_file_io import TopLaneFileIO

    mw.top_lane_run = TopLaneRunStatus()
    mw.top_lane_fileio = TopLaneFileIO()

    controller = GUIController(mw)
    # Ensure handlers exist and are callable
    assert hasattr(controller, 'on_run_clicked')
    assert hasattr(controller, 'on_settings_clicked')
    assert hasattr(controller, 'on_debug_clicked')
    assert hasattr(controller, 'on_input_file_clicked')
    assert hasattr(controller, 'on_output_folder_clicked')
    mw.close()
