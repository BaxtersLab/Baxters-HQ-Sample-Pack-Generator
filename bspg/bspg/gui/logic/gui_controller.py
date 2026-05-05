from typing import Optional
from collections import deque
from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QFileDialog, QMessageBox

from bspg.core.config import AppConfig
from bspg.core.logging import BSPGLogger, bspg_logger

from PySide6.QtCore import QObject, Signal, QThread, QTimer, QEvent

from bspg.backend_adapter.cli_runner import BackendRunner
from bspg.backend_adapter.output_parser import BackendOutputParser
from bspg.gui.workers import DemucsWorker, RepairWorker, SlicerWorker
from bspg.link.hrt_connector import HRTConnector


class GUIController:
    """Coordinates GUI widgets, backend runner, config, and logging.

    Add-only; must not modify existing GUI structure.
    """

    def __init__(self, main_window, app_config: Optional[AppConfig] = None, logger: Optional[BSPGLogger] = None):
        self.main_window = main_window
        # prefer injected AppConfig instance; fallback for tests
        try:
            if app_config is not None:
                self.app_config = app_config
            else:
                self.app_config = AppConfig()
        except Exception:
            self.app_config = AppConfig()
        self.logger = logger or bspg_logger
        # in-memory ring buffer for recent HRT connector logs
        try:
            self.hrt_log_buffer = deque(maxlen=200)
        except Exception:
            self.hrt_log_buffer = deque(maxlen=200)

        # HRT status tracking
        try:
            self.hrt_is_linked = False
            self.hrt_last_attempt = None
            self.hrt_last_success = None
        except Exception:
            self.hrt_is_linked = False
            self.hrt_last_attempt = None
            self.hrt_last_success = None
        # Backend runner (created later in F-3)
        self.backend_runner = None

        # Output parser (created later in F-4)
        self.output_parser = None

        # Initial wiring
        self.init_hooks()
        # HRT connector (auto-link background thread)
        try:
            self.hrt = HRTConnector(self)
        except Exception:
            self.hrt = None
        # initialize backend components
        try:
            self.init_backend()
        except Exception:
            pass
        # Do NOT auto-load config here; load should happen once at startup.
        # keep load_config() available but do not call it automatically.

    def init_backend(self):
        """Initialize backend runner and output parser. Add-only; do not modify existing GUI."""
        if self.backend_runner is None:
            try:
                self.backend_runner = BackendRunner()
            except Exception:
                self.backend_runner = None

        if self.output_parser is None:
            try:
                self.output_parser = BackendOutputParser()
            except Exception:
                self.output_parser = None

    class _UIRelay(QObject):
        """Thin QObject bridge that lives in the main thread.

        Because GUIController is not a QObject, signals connected directly to
        its methods use a *direct* connection and fire on the worker thread.
        Routing through this relay forces Qt to use a *queued* connection for
        the worker → relay hop, so relay signals are emitted on the main thread
        and the plain-Python callbacks below are then called safely.
        """
        sig_output_line = Signal(str)
        sig_finished = Signal(int)

    class _BackendWorker(QObject):
        sig_output_line = Signal(str)
        sig_finished = Signal(int)

        def __init__(self, runner: BackendRunner, args: list):
            super().__init__()
            self.runner = runner
            self.args = args

        def run(self):
            # run synchronously in worker thread and emit lines
            try:
                res = self.runner.run_command(self.args)
                for l in getattr(res, 'raw_output', []) or []:
                    self.sig_output_line.emit(l)
                for l in getattr(res, 'raw_error', []) or []:
                    self.sig_output_line.emit(l)
                exit_code = getattr(res, 'exit_code', 0)
            except Exception:
                exit_code = 1
            self.sig_finished.emit(int(exit_code))

    class _PipelineWorker(QObject):
        sig_output_line = Signal(str)
        sig_finished = Signal(int)

        def __init__(self, runner: BackendRunner, config):
            super().__init__()
            self.runner = runner
            self.config = config

        def run(self):
            import traceback as _tb
            import os as _os, datetime as _dt

            # File-based crash log — survives GUI process death
            _log_dir = _os.path.join(
                _os.path.dirname(_os.path.abspath(__file__)),
                '..', '..', '..', '..', 'pipeline_crash.log'
            )
            _log_path = _os.path.normpath(_log_dir)
            def _flog(*msgs):
                try:
                    with open(_log_path, 'a', encoding='utf-8') as _f:
                        _f.write(f"[{_dt.datetime.now().isoformat()}] " + " ".join(str(m) for m in msgs) + "\n")
                        _f.flush()
                except Exception:
                    pass

            _flog("=== PipelineWorker.run() START ===")
            try:
                _flog("calling run_pipeline")
                def _progress_cb(msg):
                    try:
                        self.sig_output_line.emit(msg)
                    except Exception:
                        pass
                res = self.runner.run_pipeline(self.config, progress_callback=_progress_cb)
                _flog(f"run_pipeline returned exit_code={getattr(res,'exit_code','?')}")
                for l in getattr(res, 'raw_output', []) or []:
                    self.sig_output_line.emit(l)
                    _flog("OUT:", l)
                for l in getattr(res, 'raw_error', []) or []:
                    self.sig_output_line.emit(l)
                    _flog("ERR:", l)
                exit_code = getattr(res, 'exit_code', 0)
            except Exception as exc:
                tb_text = _tb.format_exc()
                _flog("EXCEPTION:", tb_text)
                print('[PIPELINE ERROR]', tb_text, flush=True)
                for line in tb_text.splitlines():
                    self.sig_output_line.emit(line)
                self.sig_output_line.emit(f'PIPELINE ERROR: {exc}')
                exit_code = 1
            _flog(f"=== PipelineWorker.run() END exit_code={exit_code} ===")
            self.sig_finished.emit(int(exit_code))

    def init_hooks(self):
        print("DEBUG: init_hooks() called")
        # Run button
        top_run = getattr(self.main_window, 'top_lane_run', None)
        print(f"DEBUG: top_lane_run = {top_run}")
        if top_run is not None:
            try:
                btn = top_run.run_button
                # rewire run button to preparation orchestrator (add-only)
                # Don't try to disconnect if nothing is connected yet
                try:
                    btn.clicked.connect(self.prepare_and_run)
                except Exception:
                    # fallback to direct run_clicked if prepare_and_run unavailable
                    try:
                        btn.clicked.connect(self.on_run_clicked)
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                btn = top_run.settings_button
                print(f"DEBUG: settings_button = {btn}")
                btn.clicked.connect(self.on_settings_clicked)
                print("DEBUG: Settings button connected!")
            except Exception as e:
                print(f"DEBUG: Failed to connect settings button: {e}")
                import traceback
                traceback.print_exc()

            try:
                btn = top_run.debug_button
                btn.clicked.connect(self.on_debug_clicked)
            except Exception:
                pass

        # File IO lane
        top_fileio = getattr(self.main_window, 'top_lane_fileio', None)
        if top_fileio is not None:
            try:
                btn = top_fileio.input_button
                btn.clicked.connect(self.on_input_file_clicked)
            except Exception:
                pass
            try:
                btn = top_fileio.output_button
                btn.clicked.connect(self.on_output_folder_clicked)
            except Exception:
                pass

        # Flowchart checkbox → debug terminal logging
        try:
            fw = getattr(self.main_window, 'flowchart_widget', None)
            if fw is not None and hasattr(fw, 'sig_checkbox_changed'):
                fw.sig_checkbox_changed.connect(self._on_flowchart_checkbox_changed)
        except Exception:
            pass

        # start HRT autolink in background (non-blocking) if enabled in config
        try:
            hrt_cfg = getattr(self.app_config, 'hrt', None)
            if hrt_cfg is not None and getattr(hrt_cfg, 'autolink_enabled', False):
                try:
                    host = getattr(hrt_cfg, 'host', '127.0.0.1')
                    port = int(getattr(hrt_cfg, 'port', 5050) or 5050)
                    if hasattr(self, 'hrt') and self.hrt is not None:
                        try:
                            self.hrt.start_autolink(host=host, port=port)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    # --- Module H: Legal gating ---
    def is_terms_accepted(self) -> bool:
        try:
            return bool(getattr(self.app_config, 'terms_accepted', False))
        except Exception:
            return False

    def _get_run_button(self):
        """Return the run button widget, or None."""
        try:
            top_run = getattr(self.main_window, 'top_lane_run', None)
            if top_run is not None:
                return getattr(top_run, 'run_button', None)
        except Exception:
            pass
        return None

    def check_terms_gate(self):
        """Disable or enable the run button based on legal acceptance state."""
        btn = self._get_run_button()
        if btn is None:
            return
        if self.is_terms_accepted():
            btn.setEnabled(True)
            btn.setToolTip('')
            # Remove event filter if one was installed
            try:
                if hasattr(self, '_terms_gate_filter'):
                    btn.parent().removeEventFilter(self._terms_gate_filter)
            except Exception:
                pass
        else:
            btn.setEnabled(False)
            btn.setToolTip('You must acknowledge the Legal Agreement before running.')
            # Install event filter on parent to catch mouse-press attempts on disabled button
            try:
                self._terms_gate_filter = self._TermsGateFilter(btn, self._show_terms_required_message)
                if btn.parent():
                    btn.parent().installEventFilter(self._terms_gate_filter)
            except Exception:
                pass

    def _show_terms_required_message(self):
        """Show a message box when the user attempts to click the locked run button."""
        try:
            QMessageBox.warning(
                None,
                'Legal Agreement Required',
                'User Must Accept Legal Terms\n\nPlease open Settings and click\n"Permanently Acknowledge Legal Agreement" to unlock the run button.',
            )
        except Exception:
            pass

    class _TermsGateFilter(QObject):
        """Event filter installed on the run button\'s parent to detect clicks on the disabled run button."""
        def __init__(self, watched_btn, callback):
            super().__init__(watched_btn.parent())
            self._btn = watched_btn
            self._callback = callback

        def eventFilter(self, obj, event):
            if event.type() == QEvent.MouseButtonPress:
                try:
                    btn_rect = self._btn.rect().translated(self._btn.pos())
                    if btn_rect.contains(event.pos()) and not self._btn.isEnabled():
                        self._callback()
                        return True  # eat the event so nothing else fires
                except Exception:
                    pass
            return False

    def enforce_terms_gate(self):
        """Returns True if terms are accepted."""
        return self.is_terms_accepted()

    def lock_features(self):
        """No-op stub — kept so old call-sites don\'t crash."""
        pass

    def legal_acceptance_checkbox_changed(self, accepted: bool):
        """Legacy stub — kept so old connections don\'t crash."""
        pass

    def legal_acceptance_save_requested(self):
        """Persist the legal acceptance flag to disk, then unlock the run button."""
        try:
            self.app_config.terms_accepted = True
        except Exception:
            pass
        try:
            if hasattr(self, 'save_config'):
                self.save_config()
            elif hasattr(self.app_config, 'save'):
                self.app_config.save()
        except Exception:
            pass
        # Unlock run button now that terms are accepted
        self.check_terms_gate()

    def _unlock_run_button(self):
        """Alias for check_terms_gate — re-evaluates gate state."""
        self.check_terms_gate()

    # --- Module I: HRT auto-link callback ---
    def on_hrt_link_success(self):
        """
        Called when HRT auto-link succeeds.
        Updates beacon and enables temp-kill integration.
        """
        try:
            if hasattr(self.main_window, 'set_hrt_beacon_green'):
                try:
                    self.main_window.set_hrt_beacon_green()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            # update internal status and timestamp
            try:
                self.hrt_is_linked = True
                self.hrt_last_success = QDateTime.currentDateTime()
            except Exception:
                pass

            # forward lightweight debug message to view and show toast
            try:
                self.log_debug('HRT linked successfully via /link handshake.')
            except Exception:
                # fallback
                if hasattr(self.main_window, 'log_debug_message'):
                    try:
                        self.main_window.log_debug_message('HRT linked successfully.')
                    except Exception:
                        pass

            try:
                mw = getattr(self, 'main_window', None)
                if mw is not None and hasattr(mw, 'show_toast'):
                    try:
                        mw.show_toast('Linked to Hot Rod Tuner')
                    except Exception:
                        pass
            except Exception:
                pass

            # refresh settings panel status UI if available
            try:
                mw = getattr(self, 'main_window', None)
                if mw is not None and hasattr(mw, 'update_hrt_status_ui'):
                    try:
                        mw.update_hrt_status_ui()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def log_debug(self, message: str):
        """Forward debug messages to the main window if available."""
        try:
            # store in ring buffer
            try:
                self.hrt_log_buffer.append(message)
            except Exception:
                pass

        except Exception:
            pass

            if hasattr(self, 'main_window') and getattr(self, 'main_window') is not None and hasattr(self.main_window, 'log_debug_message'):
                try:
                    self.main_window.log_debug_message(message)
                    return
                except Exception:
                    pass
        except Exception:
            pass
        # fallback to configured logger
        try:
            if hasattr(self, 'logger') and self.logger is not None:
                try:
                    self.logger.info('debug', message)
                except Exception:
                    pass
        except Exception:
            pass

    def request_toast(self, message: str, duration_ms: int = 2500):
        """Request a transient toast to be shown on the GUI thread."""
        try:
            mw = getattr(self, 'main_window', None)
            if mw is None:
                return
            try:
                QTimer.singleShot(0, lambda: mw.show_toast(message, duration_ms))
            except Exception:
                try:
                    mw.show_toast(message, duration_ms)
                except Exception:
                    pass
        except Exception:
            pass

    def record_hrt_attempt(self):
        try:
            self.hrt_last_attempt = QDateTime.currentDateTime()
            # mark as not linked until success
            try:
                self.hrt_is_linked = False
            except Exception:
                pass
        except Exception:
            pass

    def manual_hrt_link(self, host: str, port: int):
        """Manually request an HRT link attempt without blocking the GUI."""
        # Record attempt and update in-memory values
        try:
            self.record_hrt_attempt()
        except Exception:
            pass

        # Update in-memory values
        try:
            self.hrt_host = host
            self.hrt_port = int(port)
        except Exception:
            pass

        try:
            self.log_debug(f'Manual HRT link requested to {host}:{port}.')
        except Exception:
            pass

        # Start non-blocking autolink attempt if connector exists
        try:
            hrt = getattr(self, 'hrt', None)
            if hrt is not None:
                try:
                    # mark this attempt as manual so connector may surface a toast
                    try:
                        hrt.manual_triggered = True
                    except Exception:
                        pass
                    hrt.start_autolink(host=host, port=int(port))
                except Exception:
                    pass
        except Exception:
            pass

    def get_recent_hrt_logs(self):
        try:
            return list(getattr(self, 'hrt_log_buffer', []))
        except Exception:
            return []

    def on_hrt_ping(self):
        """
        Called every 60 seconds by MainWindow.
        If not linked, attempt a reconnect using the existing autolink logic.
        Non-blocking and reuses the HRTConnector background start.
        """
        try:
            # If already linked, nothing to do
            if getattr(self, 'hrt_is_linked', False):
                return
        except Exception:
            # assume not linked if state unreadable
            pass

        try:
            # record attempt timestamp and mark not linked
            try:
                self.record_hrt_attempt()
            except Exception:
                pass

            # log the ping event
            try:
                self.log_debug('HRT ping: link not active, attempting reconnect...')
            except Exception:
                pass

            # trigger non-blocking autolink using configured host/port
            try:
                host = getattr(self, 'hrt_host', None)
                port = getattr(self, 'hrt_port', None)
                # fall back to AppConfig if needed
                if host is None or port is None:
                    try:
                        hcfg = getattr(self.app_config, 'hrt', None)
                        host = host or getattr(hcfg, 'host', '127.0.0.1')
                        port = int(getattr(hcfg, 'port', 5050) or 5050)
                    except Exception:
                        host = host or '127.0.0.1'
                        port = int(port or 5050)

                if getattr(self, 'hrt', None) is not None:
                    try:
                        self.hrt.start_autolink(host=host, port=int(port))
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    # --- Module I: expose and update HRT settings for Settings panel ---
    def get_hrt_settings(self) -> dict:
        try:
            hrt_cfg = getattr(self.app_config, 'hrt', None)
            if hrt_cfg is None:
                return {"host": '127.0.0.1', "port": 5050, "autolink_enabled": True}
            return {
                "host": getattr(hrt_cfg, 'host', '127.0.0.1'),
                "port": int(getattr(hrt_cfg, 'port', 5050) or 5050),
                "autolink_enabled": bool(getattr(hrt_cfg, 'autolink_enabled', True)),
            }
        except Exception:
            return {"host": '127.0.0.1', "port": 5050, "autolink_enabled": True}

    def update_hrt_settings(self, host: str, port: int, autolink_enabled: bool):
        try:
            hrt_cfg = getattr(self.app_config, 'hrt', None)
            if hrt_cfg is None:
                return
            try:
                hrt_cfg.host = host
                hrt_cfg.port = int(port)
                hrt_cfg.autolink_enabled = bool(autolink_enabled)
            except Exception:
                pass

            # Persist config (use AppConfig.save)
            try:
                if hasattr(self.app_config, 'save'):
                    try:
                        self.app_config.save()
                    except Exception:
                        pass
            except Exception:
                pass

            # Update in-memory connector values and restart autolink if enabled
            try:
                self.hrt_host = getattr(self, 'hrt_host', host)
                self.hrt_port = getattr(self, 'hrt_port', port)
                self.hrt_autolink_enabled = getattr(self, 'hrt_autolink_enabled', autolink_enabled)
                if getattr(self, 'hrt', None) is not None and bool(autolink_enabled):
                    try:
                        self.hrt.start_autolink(host=host, port=int(port))
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def on_run_clicked(self):
        self.logger.info('gui', 'Run button clicked.')

        # Deprecated direct run entrypoint — prefer prepare_and_run orchestration
        # Keep backward compatibility: call prepare_and_run if available
        try:
            return self.prepare_and_run()
        except Exception as _e:
            self.logger.error('gui', f'prepare_and_run raised: {_e}')

        # If prepare_and_run failed, fall back to launching backend directly
        self._launch_backend_worker()

    def _launch_backend_worker(self):
        """Initialise backend and spin up the pipeline worker thread."""
        try:
            # Sync flowchart → config before running
            self.sync_flowchart_to_config()

            # Ensure backend is initialized
            self.init_backend()

            # Start backend pipeline (prefer run_pipeline) in a worker thread (non-blocking)
            if self.backend_runner is not None and hasattr(self.backend_runner, 'run_pipeline'):
                worker = self._PipelineWorker(self.backend_runner, self.app_config)
            else:
                args = []
                if self.backend_runner is not None:
                    args = self.backend_runner.build_command(self.app_config)
                worker = self._BackendWorker(self.backend_runner, args)

            thread = QThread()
            worker.moveToThread(thread)

            # Route worker signals through a main-thread QObject relay so that
            # on_backend_output / on_backend_finished are always called on the
            # main thread (GUIController is not a QObject → direct connection
            # without relay would fire callbacks in the worker thread).
            relay = self._UIRelay()
            self._ui_relay = relay  # keep reference so it isn't GC'd

            thread.started.connect(worker.run)
            worker.sig_output_line.connect(relay.sig_output_line)   # queued: worker → main
            relay.sig_output_line.connect(self.on_backend_output)   # direct:  main  → main
            worker.sig_finished.connect(relay.sig_finished)         # queued: worker → main
            relay.sig_finished.connect(self.on_backend_finished)    # direct:  main  → main
            worker.sig_finished.connect(thread.quit)
            worker.sig_finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            # NOTE: relay is intentionally NOT connected to deleteLater here.
            # Deleting the relay while sig_finished is still dispatching causes
            # a segfault on Windows.  on_backend_finished cleans it up instead.

            thread.start()
            self._backend_thread = thread
            self._backend_worker = worker
        except Exception as _e:
            self.logger.error('gui', f'Failed to start backend worker: {_e}')

    def prepare_and_run(self):
        """Full pre-run sequence: validate, sync, reset, then run."""

        # Gate: terms must be acknowledged before running
        if not self.is_terms_accepted():
            self._show_terms_required_message()
            return

        self.logger.info('gui', 'Preparing pipeline run.')

        # Sync settings → config
        try:
            self.sync_settings_to_config()
        except Exception:
            pass

        # Sync flowchart → config
        try:
            self.sync_flowchart_to_config()
        except Exception:
            pass

        # Gate: at least one flowchart checkbox must be checked
        try:
            fc = getattr(self.app_config, 'flowchart', None)
            if fc is not None:
                any_checked = any(
                    getattr(fc, f'cb{i}', False) for i in range(1, 9)
                )
                if not any_checked:
                    QMessageBox.warning(
                        None,
                        'No Pipeline Stage Selected',
                        'No boxes checked.\n\nPlease select at least one stage on the flowchart before running.',
                    )
                    return
        except Exception:
            pass

        # Validate config
        try:
            if not self.validate_config():
                self.logger.error('gui', 'Run aborted due to invalid configuration.')
                return
        except Exception:
            self.logger.error('gui', 'Validation error; aborting run.')
            return

        # Reset GUI indicators
        try:
            self.reset_pipeline_status()
        except Exception:
            pass

        # Optionally disable run button to prevent double-run
        try:
            self.disable_run_button()
        except Exception:
            pass

        # Save config before running
        try:
            self.save_config()
        except Exception:
            pass

        # Start backend
        try:
            return self._launch_backend_worker()
        except Exception as _e:
            self.logger.error('gui', f'Failed to start run after preparation: {_e}')
            try:
                self.post_run_cleanup(None)
            except Exception:
                pass

    def _start_worker(self, worker_obj, run_in_thread: bool = True):
        """Start a BaseWorker-derived object either in a QThread (non-blocking)
        or run synchronously (for testing).
        """
        try:
            if not run_in_thread:
                # synchronous execution (test-friendly)
                res = worker_obj.run()
                try:
                    # propagate finished result to controller
                    self.update_pipeline_status(res)
                except Exception:
                    pass
                return res

            # run in a thread
            thread = QThread()
            worker_obj.moveToThread(thread)
            thread.started.connect(worker_obj.run)
            worker_obj.sig_finished.connect(thread.quit)
            worker_obj.sig_finished.connect(worker_obj.deleteLater)
            thread.finished.connect(thread.deleteLater)
            worker_obj.sig_finished.connect(lambda r: self.update_pipeline_status(r))
            thread.start()
            # keep reference
            if not hasattr(self, '_worker_threads'):
                self._worker_threads = []
            self._worker_threads.append((thread, worker_obj))
            return None
        except Exception:
            return None

    def start_demucs_worker(self, run_in_thread: bool = True):
        try:
            w = DemucsWorker(config=self.app_config.paths.__dict__ if hasattr(self.app_config, 'paths') else None)
            return self._start_worker(w, run_in_thread=run_in_thread)
        except Exception:
            return None

    def start_repair_worker(self, run_in_thread: bool = True):
        try:
            w = RepairWorker(config={})
            return self._start_worker(w, run_in_thread=run_in_thread)
        except Exception:
            return None

    def start_slicer_worker(self, run_in_thread: bool = True):
        try:
            w = SlicerWorker(config={})
            return self._start_worker(w, run_in_thread=run_in_thread)
        except Exception:
            return None

    def on_settings_clicked(self):
        self.logger.info('gui', 'Settings button clicked.')
        print("DEBUG: Settings button clicked!")  # Debug output

        # Always open the settings panel (do not merely toggle off when gating is active)
        if hasattr(self.main_window, 'settings_panel'):
            print(f"DEBUG: main_window has settings_panel")
            try:
                panel = self.main_window.settings_panel
                print(f"DEBUG: panel = {panel}")
                print(f"DEBUG: panel parent = {panel.parent()}")
                print(f"DEBUG: panel geometry = {panel.geometry()}")
                try:
                    # Simple toggle: hide if visible, else show.
                    try:
                        visible = panel.isVisible()
                        print(f"DEBUG: panel.isVisible() = {visible}")
                    except Exception as e:
                        print(f"DEBUG: Error checking visibility: {e}")
                        visible = False
                    try:
                        panel.setVisible(not visible)
                        print(f"DEBUG: panel.setVisible({not visible}) called")
                        
                        # Hide logo and flowchart when settings is open to give it more space
                        if hasattr(self.main_window, 'logo_container'):
                            try:
                                self.main_window.logo_container.setVisible(visible)  # Hide when panel visible
                                print(f"DEBUG: logo_container visibility = {visible}")
                            except Exception as e:
                                print(f"DEBUG: Error toggling logo_container: {e}")
                        
                        if hasattr(self.main_window, 'flowchart_container'):
                            try:
                                self.main_window.flowchart_container.setVisible(visible)  # Hide when panel visible
                                print(f"DEBUG: flowchart_container visibility = {visible}")
                            except Exception as e:
                                print(f"DEBUG: Error toggling flowchart_container: {e}")
                        
                        # CRITICAL: Raise panel above overlay so it's visible
                        if not visible:  # We just made it visible
                            # Lower the overlay if present so panel can be seen
                            if hasattr(self.main_window, '_terms_overlay') and self.main_window._terms_overlay is not None:
                                print("DEBUG: Found terms overlay, lowering it")
                                self.main_window._terms_overlay.lower()
                            
                            panel.raise_()
                            print("DEBUG: panel.raise_() called")
                            print(f"DEBUG: panel.isVisible() after raise = {panel.isVisible()}")
                            print(f"DEBUG: panel geometry after raise = {panel.geometry()}")
                    except Exception as e:
                        print(f"DEBUG: Error setting visibility: {e}")
                        import traceback
                        traceback.print_exc()

                    # If we've just shown the panel and terms are not accepted, navigate to Legal
                    try:
                        if not visible and not self.is_terms_accepted():
                            print("DEBUG: Terms not accepted, navigating to legal")
                            if hasattr(self.main_window, 'navigate_to_legal_settings'):
                                try:
                                    self.main_window.navigate_to_legal_settings()
                                    print("DEBUG: navigate_to_legal_settings() called")
                                except Exception as e:
                                    print(f"DEBUG: Error navigating: {e}")
                    except Exception as e:
                        print(f"DEBUG: Error in terms check: {e}")
                except Exception:
                    pass
            except Exception:
                pass

    def on_debug_clicked(self):
        self.logger.info('gui', 'Debug button clicked.')

        # Toggle debug terminal container visibility if present
        if hasattr(self.main_window, 'debug_terminal_container'):
            try:
                cont = self.main_window.debug_terminal_container
                cont.setVisible(not cont.isVisible())
            except Exception:
                pass

    def on_input_file_clicked(self):
        self.logger.info('gui', 'Input file button clicked.')

        try:
            dlg = QFileDialog(self.main_window)
            dlg.setFileMode(QFileDialog.ExistingFiles)
            if dlg.exec():
                files = dlg.selectedFiles()
                try:
                    self.app_config.paths.input_files = files
                except Exception:
                    try:
                        self.app_config.input_files = files
                    except Exception:
                        pass
                self.logger.info('gui', f'Selected input files: {files}')
                # update display box
                try:
                    self.main_window.top_lane_fileio.set_input_files_display(files)
                except Exception:
                    pass
        except Exception:
            pass
    def on_output_folder_clicked(self):
        self.logger.info('gui', 'Output folder button clicked.')

        try:
            folder = QFileDialog.getExistingDirectory(self.main_window, 'Select Output Folder')
            if folder:
                try:
                    self.app_config.paths.output_folder = folder
                except Exception:
                    try:
                        self.app_config.output_folder = folder
                    except Exception:
                        pass
                self.logger.info('gui', f'Selected output folder: {folder}')
                # update display box
                try:
                    self.main_window.top_lane_fileio.set_output_folder_display(folder)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_flowchart_checkbox_changed(self, msg: str):
        """Route flowchart checkbox toggle messages to the debug terminal."""
        try:
            if hasattr(self.main_window, 'log_debug_message'):
                self.main_window.log_debug_message(msg)
        except Exception:
            pass

    def sync_flowchart_to_config(self):
        """Sync flowchart checkbox states to AppConfig with gating logic."""
        if not hasattr(self.main_window, 'flowchart_widget'):
            return

        fc = self.main_window.flowchart_widget
        try:
            # Read all checkboxes
            states = {}
            for i in range(1, 9):
                cb_name = f'flowchart_cb_{i}'
                cb = getattr(fc, cb_name, None)
                if cb is None and hasattr(fc, cb_name):
                    cb = getattr(fc, cb_name)
                if cb is not None and hasattr(cb, 'isChecked'):
                    states[i] = bool(cb.isChecked())

            # Apply gating logic (mutual exclusion examples)
            if states.get(2) and states.get(4):
                states[4] = False
            if states.get(2) and states.get(7):
                states[7] = False
            if states.get(4) and states.get(7):
                states[7] = False

            # Write into AppConfig
            for i, val in states.items():
                try:
                    if hasattr(self.app_config, 'set_checkbox_state'):
                        self.app_config.set_checkbox_state(i, val)
                    else:
                        if hasattr(self.app_config, 'flowchart'):
                            setattr(self.app_config.flowchart, f'cb{i}', val)
                except Exception:
                    try:
                        if hasattr(self.app_config, 'flowchart'):
                            setattr(self.app_config.flowchart, f'cb{i}', val)
                    except Exception:
                        pass

            self.logger.info('gui', 'Flowchart synced to AppConfig with gating logic.')
        except Exception:
            pass

    def sync_settings_to_config(self):
        """Read settings panel widgets and update AppConfig. Add-only; do not modify existing GUI."""
        if not hasattr(self.main_window, 'settings_panel'):
            return

        panel = self.main_window.settings_panel
        try:
            if hasattr(panel, 'sample_rate_input'):
                val = None
                try:
                    val = panel.sample_rate_input.value()
                except Exception:
                    try:
                        val = panel.sample_rate_input.text()
                    except Exception:
                        pass
                if val is not None:
                    try:
                        if hasattr(self.app_config, 'settings'):
                            setattr(self.app_config.settings, 'sample_rate', val)
                        else:
                            setattr(self.app_config, 'sample_rate', val)
                    except Exception:
                        pass

            if hasattr(panel, 'bit_depth_input'):
                try:
                    val = panel.bit_depth_input.value()
                    if hasattr(self.app_config, 'settings'):
                        setattr(self.app_config.settings, 'bit_depth', val)
                    else:
                        setattr(self.app_config, 'bit_depth', val)
                except Exception:
                    pass

            if hasattr(panel, 'output_format_dropdown'):
                try:
                    val = panel.output_format_dropdown.currentText()
                    if hasattr(self.app_config, 'settings'):
                        setattr(self.app_config.settings, 'output_format', val)
                    else:
                        setattr(self.app_config, 'output_format', val)
                except Exception:
                    pass

            if hasattr(panel, 'enable_hrtf_checkbox'):
                try:
                    val = bool(panel.enable_hrtf_checkbox.isChecked())
                    if hasattr(self.app_config, 'hrt'):
                        setattr(self.app_config.hrt, 'auto_connect', val)
                    else:
                        setattr(self.app_config, 'enable_hrtf', val)
                except Exception:
                    pass

            self.logger.info('gui', 'Settings synced to AppConfig.')
        except Exception:
            pass

    def sync_config_to_settings(self):
        """Populate settings panel widgets from AppConfig. Add-only; do not modify existing GUI."""
        if not hasattr(self.main_window, 'settings_panel'):
            return

        panel = self.main_window.settings_panel
        try:
            if hasattr(panel, 'sample_rate_input'):
                try:
                    val = None
                    if hasattr(self.app_config, 'settings') and hasattr(self.app_config.settings, 'sample_rate'):
                        val = getattr(self.app_config.settings, 'sample_rate')
                    elif hasattr(self.app_config, 'sample_rate'):
                        val = getattr(self.app_config, 'sample_rate')
                    if val is not None:
                        try:
                            panel.sample_rate_input.setValue(val)
                        except Exception:
                            try:
                                panel.sample_rate_input.setText(str(val))
                            except Exception:
                                pass
                except Exception:
                    pass

            if hasattr(panel, 'bit_depth_input'):
                try:
                    if hasattr(self.app_config, 'settings') and hasattr(self.app_config.settings, 'bit_depth'):
                        panel.bit_depth_input.setValue(self.app_config.settings.bit_depth)
                except Exception:
                    pass

            if hasattr(panel, 'output_format_dropdown'):
                try:
                    if hasattr(self.app_config, 'settings') and hasattr(self.app_config.settings, 'output_format'):
                        panel.output_format_dropdown.setCurrentText(self.app_config.settings.output_format)
                except Exception:
                    pass

            if hasattr(panel, 'enable_hrtf_checkbox'):
                try:
                    if hasattr(self.app_config, 'hrt') and hasattr(self.app_config.hrt, 'auto_connect'):
                        panel.enable_hrtf_checkbox.setChecked(bool(self.app_config.hrt.auto_connect))
                except Exception:
                    pass

            self.logger.info('gui', 'Settings panel updated from AppConfig.')
        except Exception:
            pass

    def validate_config(self) -> bool:
        """Validate AppConfig before running backend. Returns True if valid."""
        try:
            # prefer an external ConfigValidator if available
            try:
                from bspg.core.config_validator import ConfigValidator
                validator = ConfigValidator(self.logger)
                ok, msg = validator.validate(self.app_config)
                if not ok:
                    self.logger.error('config', f'Configuration invalid: {msg}')
                    return False
                return True
            except Exception:
                # fallback simple checks
                paths = getattr(self.app_config, 'paths', None)
                if not paths or not getattr(paths, 'input_files', None):
                    self.logger.error('config', 'Configuration invalid: no input files')
                    return False
                out = getattr(paths, 'output_folder', None)
                if not out:
                    self.logger.error('config', 'Configuration invalid: no output folder')
                    return False
                return True
        except Exception as e:
            self.logger.error('config', f'Validation exception: {e}')
            return False

    def save_config(self):
        """Save AppConfig to disk. Add-only."""
        try:
            if hasattr(self.app_config, 'save'):
                try:
                    self.app_config.save()
                    self.logger.info('config', 'Configuration saved.')
                except Exception as e:
                    self.logger.error('config', f'Failed to save config: {e}')
            else:
                self.logger.info('config', 'No save() on AppConfig; skipping save.')
        except Exception:
            pass

    def load_config(self):
        """Load AppConfig from disk. Add-only."""
        try:
            if hasattr(self.app_config, 'load'):
                try:
                    self.app_config.load()
                    self.logger.info('config', 'Configuration loaded.')
                    self.sync_config_to_settings()
                except Exception as e:
                    self.logger.error('config', f'Failed to load config: {e}')
            else:
                self.logger.info('config', 'No load() on AppConfig; skipping load.')
        except Exception:
            pass

    def update_pipeline_status(self, status):
        """Update GUI elements based on pipeline status."""
        try:
            # status may be a PipelineState or a simple stage value
            stage = getattr(status, 'stage', status)
            progress = getattr(status, 'progress', None)

            # Status label
            if hasattr(self.main_window, 'top_lane_run'):
                try:
                    self.main_window.top_lane_run.update_status(str(stage))
                except Exception:
                    pass

            # Thermometer
            if hasattr(self.main_window, 'top_lane_fileio') and progress is not None:
                try:
                    self.main_window.top_lane_fileio.update_thermometer(progress)
                except Exception:
                    pass
            # Progress bar
            if hasattr(self.main_window, 'top_lane_run') and progress is not None:
                try:
                    self.main_window.top_lane_run.update_progress(progress)
                except Exception:
                    pass
        except Exception:
            pass

    def reset_pipeline_status(self):
        """Reset status indicators before a run."""
        try:
            if hasattr(self.main_window, 'top_lane_run'):
                try:
                    self.main_window.top_lane_run.update_status('Starting')
                except Exception:
                    pass
                try:
                    self.main_window.top_lane_run.reset_progress()
                except Exception:
                    pass
            if hasattr(self.main_window, 'top_lane_fileio'):
                try:
                    self.main_window.top_lane_fileio.update_thermometer(0.0)
                except Exception:
                    pass
            # clear debug terminal
            try:
                self.clear_debug_terminal()
            except Exception:
                pass
        except Exception:
            pass

    def disable_run_button(self):
        try:
            if hasattr(self.main_window, 'top_lane_run'):
                try:
                    self.main_window.top_lane_run.run_button.setEnabled(False)
                except Exception:
                    pass
        except Exception:
            pass

    def post_run_cleanup(self, state):
        """Cleanup after backend finishes. `state` may be None or a PipelineState."""
        try:
            # Re-enable run button
            try:
                if hasattr(self.main_window, 'top_lane_run'):
                    self.main_window.top_lane_run.run_button.setEnabled(True)
            except Exception:
                pass

            # Auto-save config if possible
            try:
                self.save_config()
            except Exception:
                pass

            self.logger.info('gui', 'Post-run cleanup complete.')
        except Exception:
            pass

    def on_backend_output(self, line: str):
        """Handle raw backend output lines: forward to debug terminal, stdout, and parser."""
        # Always print to the launch terminal so nothing is invisible
        print(f'[pipeline] {line}', flush=True)

        # Forward to in-app debug terminal widget if present
        try:
            mw = getattr(self, 'main_window', None)
            if mw is not None:
                if hasattr(mw, 'log_debug_message'):
                    try:
                        mw.log_debug_message(line)
                    except Exception:
                        pass
                elif hasattr(mw, 'debug_terminal_widget'):
                    try:
                        mw.debug_terminal_widget.append(line)
                    except Exception:
                        pass
        except Exception:
            pass

        # Also run through output parser for status/progress updates
        try:
            if self.output_parser is not None:
                evt = self.output_parser.parse_line(line)
                state = self.output_parser.update_state(evt)
                try:
                    self.update_pipeline_status(state)
                except Exception:
                    pass
            else:
                self.logger.info('backend', line)
        except Exception:
            pass

    def on_backend_finished(self, exit_code: int):
        """Handle backend completion, update state, handle errors, and cleanup."""
        print(f'[pipeline] finished exit_code={exit_code}', flush=True)
        try:
            state = None
            if self.output_parser is not None:
                try:
                    state = self.output_parser.finalize(exit_code)
                except Exception:
                    state = None

            # update GUI
            try:
                self.update_pipeline_status(state or exit_code)
            except Exception:
                pass

            # Error handling — print and forward to debug terminal
            try:
                if exit_code != 0 or (hasattr(state, 'error') and getattr(state, 'error') is not None):
                    err_detail = getattr(state, 'error', None) or f'exit code {exit_code}'
                    msg = f'Pipeline finished with errors: {err_detail}'
                    print(f'[ERROR] {msg}', flush=True)
                    self.logger.error('pipeline', msg)
                    try:
                        mw = getattr(self, 'main_window', None)
                        if mw is not None and hasattr(mw, 'log_debug_message'):
                            mw.log_debug_message(f'ERROR: {msg}')
                    except Exception:
                        pass
                else:
                    print('[pipeline] SUCCESS', flush=True)
            except Exception:
                pass

            # Cleanup
            try:
                self.post_run_cleanup(state)
            except Exception:
                pass

            # Safe relay teardown — now that all signal dispatching is done
            try:
                relay = getattr(self, '_ui_relay', None)
                if relay is not None:
                    relay.deleteLater()
                    self._ui_relay = None
            except Exception:
                pass

            self.logger.info('gui', f'Backend finished with exit code {exit_code}.')
        except Exception:
            pass

    def clear_debug_terminal(self):
        """Clear the debug terminal if present."""
        try:
            if hasattr(self.main_window, 'debug_terminal_widget'):
                self.main_window.debug_terminal_widget.clear()
        except Exception:
            pass

    def abort_backend(self):
        """Abort backend execution if supported."""
        try:
            if getattr(self, 'backend_runner', None) and hasattr(self.backend_runner, 'abort'):
                try:
                    self.backend_runner.abort()
                except Exception:
                    pass
            # try to stop worker thread if present
            if getattr(self, '_backend_thread', None):
                try:
                    th = self._backend_thread
                    th.quit()
                except Exception:
                    pass
        except Exception:
            pass


