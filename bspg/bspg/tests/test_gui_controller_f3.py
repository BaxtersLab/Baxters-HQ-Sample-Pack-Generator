from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.main_window import MainWindow
from bspg.gui.logic.gui_controller import GUIController


def test_init_backend():
    app = QApplication.instance() or QApplication(sys.argv)
    mw = MainWindow()
    controller = GUIController(mw)
    # backend_runner and output_parser should be initialized (or at least present)
    assert hasattr(controller, 'backend_runner')
    assert hasattr(controller, 'output_parser')
    # abort_backend should not raise even if runner is None
    try:
        controller.abort_backend()
    except Exception:
        assert False, 'abort_backend raised'
