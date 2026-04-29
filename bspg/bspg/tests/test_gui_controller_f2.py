from PySide6.QtWidgets import QApplication
import sys

from bspg.gui.main_window import MainWindow
from bspg.gui.logic.gui_controller import GUIController
from bspg.core.config import AppConfig


class DummyPanel:
    def __init__(self):
        self._visible = False

    def isVisible(self):
        return self._visible

    def setVisible(self, v: bool):
        self._visible = bool(v)


class DummyContainer(DummyPanel):
    pass


class FakeQFileDialog:
    def __init__(self, parent=None):
        self._files = []

    def setFileMode(self, mode):
        pass

    def exec(self):
        return True

    def selectedFiles(self):
        return ["/tmp/a.wav", "/tmp/b.wav"]

    @staticmethod
    def getExistingDirectory(*args, **kwargs):
        return '/tmp/out'


def test_settings_and_debug_toggle_and_file_dialog(monkeypatch):
    app = QApplication.instance() or QApplication(sys.argv)
    mw = MainWindow()
    mw.settings_panel = DummyPanel()
    mw.debug_terminal_container = DummyContainer()

    # attach fileio lane
    from bspg.gui.top_lanes.lane2_file_io import TopLaneFileIO
    mw.top_lane_fileio = TopLaneFileIO()

    controller = GUIController(mw, app_config=AppConfig())

    # toggle settings
    controller.on_settings_clicked()
    assert mw.settings_panel.isVisible() is True
    controller.on_settings_clicked()
    assert mw.settings_panel.isVisible() is False

    # toggle debug
    controller.on_debug_clicked()
    assert mw.debug_terminal_container.isVisible() is True
    controller.on_debug_clicked()
    assert mw.debug_terminal_container.isVisible() is False

    # monkeypatch QFileDialog to return files
    import bspg.gui.logic.gui_controller as gc_mod

    # Monkeypatch QFileDialog class to our FakeQFileDialog
    monkeypatch.setattr(gc_mod, 'QFileDialog', FakeQFileDialog)
    controller.on_input_file_clicked()
    assert isinstance(controller.app_config.paths.input_files, list)

    # monkeypatch getExistingDirectory
    # (The following line might be redundant now, but we keep it or remove it)
    # monkeypatch.setattr(gc_mod.QFileDialog, 'getExistingDirectory', staticmethod(lambda *a, **k: '/tmp/out'))
    
    controller.on_output_folder_clicked()
    assert controller.app_config.paths.output_folder == '/tmp/out'
