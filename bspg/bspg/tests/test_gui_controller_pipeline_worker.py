from types import SimpleNamespace
import threading

from bspg.gui.logic.gui_controller import GUIController


class DummyRunner:
    def __init__(self):
        self.called = False

    def run_pipeline(self, config):
        self.called = True
        # minimal BackendProcessResult-like object
        return SimpleNamespace(exit_code=0, raw_output=['ok'], raw_error=[])


def test_pipeline_worker_calls_run_pipeline():
    # minimal main_window stub
    main_window = SimpleNamespace()
    main_window.top_lane_run = SimpleNamespace()
    main_window.top_lane_run.run_button = SimpleNamespace()
    main_window.top_lane_run.run_button.clicked = SimpleNamespace()
    # provide a connect method used during init_hooks
    def connect(fn):
        # store fn for potential use; not invoked automatically
        main_window.top_lane_run.run_button._connected = fn

    main_window.top_lane_run.run_button.clicked.connect = connect

    ctrl = GUIController(main_window)
    # monkeypatch backend_runner with dummy
    dr = DummyRunner()
    ctrl.backend_runner = dr

    # construct pipeline worker and run synchronously
    worker = ctrl._PipelineWorker(ctrl.backend_runner, ctrl.app_config)
    # call run directly (synchronous) to emulate thread execution
    worker.run()
    assert dr.called
