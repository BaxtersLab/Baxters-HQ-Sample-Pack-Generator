from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.main_window import MainWindow
from bspg.gui.logic.gui_controller import GUIController


def test_start_workers_sync():
    app = QApplication.instance() or QApplication(sys.argv)
    mw = MainWindow()
    ctrl = GUIController(mw)

    res_d = ctrl.start_demucs_worker(run_in_thread=False)
    res_r = ctrl.start_repair_worker(run_in_thread=False)
    res_s = ctrl.start_slicer_worker(run_in_thread=False)

    assert isinstance(res_d, dict) and res_d.get('status') == 'ok'
    assert isinstance(res_r, dict) and res_r.get('status') == 'ok'
    assert isinstance(res_s, dict) and res_s.get('status') == 'ok'
