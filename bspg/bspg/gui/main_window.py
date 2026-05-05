from PySide6.QtWidgets import (
    QMainWindow,
    QHBoxLayout,
    QWidget,
    QVBoxLayout,
    QAbstractButton,
    QAbstractSpinBox,
    QSlider,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QCheckBox,
    QRadioButton,
    QTabWidget,
    QToolBar,
    QMenuBar,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt, QPoint, QTimer, QDateTime
from PySide6.QtGui import QBitmap, QPainter

from bspg.core.config import AppConfig
from bspg.core.logging import bspg_logger
from bspg.gui.flowchart.flowchart_widget import FlowchartWidget


class MainWindowPlaceholder(QWidget):
    """Placeholder main window class for BSPG GUI package."""
    pass


class _HQTitleBar(QWidget):
    """Custom draggable title bar matching the Remixer app style."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('HQTitleBar')
        self.setFixedHeight(36)
        self._main_window = parent
        self._drag_start = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 6, 0)
        layout.setSpacing(4)

        title = QLabel('Baxters HQ Sample Pack Generator')
        title.setObjectName('HQTitleLabel')
        layout.addWidget(title)
        layout.addStretch()

        min_btn = QPushButton('_')
        min_btn.setObjectName('TitleBarMin')
        min_btn.setFixedSize(36, 26)
        min_btn.clicked.connect(parent.showMinimized)
        layout.addWidget(min_btn)

        max_btn = QPushButton('[ ]')
        max_btn.setObjectName('TitleBarMin')
        max_btn.setFixedSize(44, 26)
        max_btn.clicked.connect(
            lambda: parent.showNormal() if parent.isMaximized() else parent.showMaximized()
        )
        layout.addWidget(max_btn)

        close_btn = QPushButton('X')
        close_btn.setObjectName('TitleBarClose')
        close_btn.setFixedSize(36, 26)
        close_btn.clicked.connect(parent.close)
        layout.addWidget(close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint() - self._main_window.pos()

    def mouseMoveEvent(self, event):
        if self._drag_start is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self._main_window.move(event.globalPosition().toPoint() - self._drag_start)

    def mouseReleaseEvent(self, event):
        self._drag_start = None



class MainWindow(QMainWindow):
    def __init__(self, parent=None, app_config=None):
        super().__init__(parent)
        self.setWindowTitle('Baxters HQ Sample Pack Generator')
        self.setMinimumSize(800, 750)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # preserve original title for warning toggle
        self._original_title = self.windowTitle()

        # Use provided AppConfig instance when available; fallback for tests
        try:
            if app_config is not None:
                self.app_config = app_config
            else:
                self.app_config = AppConfig()
        except Exception:
            self.app_config = AppConfig()
        self.logger = bspg_logger

        # central widget and main layout
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName('CentralWidget')
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        # Reserve bottom 200px for the floating debug overlay so the flowchart
        # never extends into that zone regardless of whether the overlay is shown.
        self._DEBUG_OVERLAY_H = 230
        self.main_layout.setContentsMargins(0, 0, 0, self._DEBUG_OVERLAY_H + 60)
        # Title bar — first item in layout
        self._title_bar = _HQTitleBar(self)
        self.main_layout.addWidget(self._title_bar)
        
        # Load stylesheet for black borders, rounded edges, etc.
        try:
            self._load_stylesheet()
        except Exception as e:
            print(f"WARNING: Failed to load stylesheet: {e}")

        # containers
        self.top_lane_container = None
        self.logo_container = None
        self.flowchart_container = None
        self.debug_terminal_container = None
        self.settings_panel = None

        self.init_top_lanes()
        self.init_logo()
        self.init_flowchart()
        self.init_debug_terminal()
        self.init_settings_panel()
        # Load and display backdrop image
        try:
            self.load_backdrop()
        except Exception as e:
            try:
                self.logger.info('gui', f'Backdrop not loaded: {e}')
            except Exception:
                pass
        # Initialize controller and mark system ready (add-only)
        try:
            self.init_controller()
        except Exception as e:
            # FIX: Log exceptions instead of silently swallowing
            try:
                self.logger.error('gui', f'Failed to initialize controller: {e}')
            except Exception:
                print(f'ERROR: Failed to initialize controller: {e}')
        try:
            self.system_ready()
        except Exception as e:
            # FIX: Log exceptions instead of silently swallowing
            try:
                self.logger.error('gui', f'Failed to mark system ready: {e}')
            except Exception:
                print(f'ERROR: Failed to mark system ready: {e}')

        # HRT ping timer: periodically verify link state and trigger reconnects
        try:
            if hasattr(self, 'controller') and self.controller is not None:
                try:
                    self.hrt_ping_timer = QTimer(self)
                    self.hrt_ping_timer.setInterval(60000)  # 60 seconds
                    try:
                        # connect to controller handler (non-blocking)
                        self.hrt_ping_timer.timeout.connect(self.controller.on_hrt_ping)
                    except Exception:
                        pass
                    try:
                        self.hrt_ping_timer.start()
                    except Exception:
                        pass
                except Exception:
                    self.hrt_ping_timer = None
        except Exception:
            self.hrt_ping_timer = None

    def _load_stylesheet(self):
        """Load the stylesheet from gui/styles.qss"""
        try:
            import os
            # Navigate from bspg/bspg/gui/main_window.py -> gui/styles.qss
            # bspg/bspg/gui/ -> bspg/bspg/ -> bspg/ -> project root -> gui/
            current_dir = os.path.dirname(__file__)  # bspg/bspg/gui/
            gui_dir = os.path.join(current_dir, '..', '..', '..', 'gui')  # project_root/gui/
            styles_path = os.path.join(gui_dir, 'styles.qss')
            styles_path = os.path.abspath(styles_path)
            
            if os.path.exists(styles_path):
                with open(styles_path, 'r') as f:
                    stylesheet = f.read()
                    self.setStyleSheet(stylesheet)
                    print(f"INFO: Loaded stylesheet from {styles_path}")
            else:
                print(f"WARNING: Stylesheet not found at {styles_path}")
        except Exception as e:
            print(f"ERROR: Failed to load stylesheet: {e}")
            import traceback
            traceback.print_exc()

    def init_top_lanes(self):
        self.top_lane_container = QWidget(self)
        self.top_lane_container.setObjectName('top_lane_container')
        # Styling is handled by global stylesheet (gui/styles.qss)
        # Don't set inline stylesheet here - it overrides button styles
        self.top_lane_container.setLayout(QVBoxLayout())
        self.main_layout.addWidget(self.top_lane_container)
        
        # FIX: Instantiate and add the actual top lane widgets
        try:
            from bspg.gui.top_lanes.lane1_run_status import TopLaneRunStatus
            from bspg.gui.top_lanes.lane2_file_io import TopLaneFileIO
            
            self.top_lane_run = TopLaneRunStatus(parent=self, app_config=self.app_config)
            self.top_lane_fileio = TopLaneFileIO(parent=self, app_config=self.app_config)
            
            # Add to the container
            self.top_lane_container.layout().addWidget(self.top_lane_run)
            self.top_lane_container.layout().addWidget(self.top_lane_fileio)
        except Exception as e:
            # Log but continue - at least show empty containers
            try:
                self.logger.error('gui', f'Failed to instantiate top lanes: {e}')
            except Exception:
                pass
        
        # Terms banner placeholder (added but hidden)
        try:
            from PySide6.QtWidgets import QLabel
            self.terms_banner = QLabel('', self)
            self.terms_banner.setObjectName('terms_banner')
            self.terms_banner.setVisible(False)
            # Set height to 0 when hidden so it doesn't create a gap
            self.terms_banner.setMaximumHeight(0)
            self.terms_banner.setStyleSheet('color: white; background-color: red; padding: 6px;')
            self.main_layout.insertWidget(1, self.terms_banner)
            self._terms_banner_timer = None
            self._settings_pulse_timer = None
        except Exception:
            self.terms_banner = None
            self._terms_banner_timer = None
            self._settings_pulse_timer = None

    def init_logo(self):
        # Preserve existing logo container if present
        if getattr(self, 'logo_container', None) is None:
            self.logo_container = QWidget(self)
            self.logo_container.setObjectName('logo_container')
            self.logo_container.setLayout(QVBoxLayout())
            # Make transparent so backdrop image shows through
            self.logo_container.setStyleSheet("background: transparent;")
            # Minimum height just enough for the logo to breathe;
            # Expanding policy lets it absorb all flex space so the
            # flowchart stays compact above the debug overlay zone.
            self.logo_container.setMinimumHeight(80)
            from PySide6.QtWidgets import QSizePolicy
            _sp = self.logo_container.sizePolicy()
            _sp.setVerticalPolicy(QSizePolicy.Policy.Expanding)
            self.logo_container.setSizePolicy(_sp)
            self.main_layout.addWidget(self.logo_container)

        # logo_label helper reference (added only if missing)
        if not hasattr(self, 'logo_label'):
            from PySide6.QtWidgets import QLabel

            self.logo_label = QLabel(self.logo_container)
            self.logo_label.setObjectName('logo_label')
            # do not add to layout here; preserve existing styling/layout

    def init_flowchart(self):
        # Create signal routing flowchart widget
        try:
            self.flowchart_widget = FlowchartWidget(app_config=self.app_config, logger=self.logger, parent=self)
            self.flowchart_widget.setObjectName('flowchart_container')
            # Make transparent so backdrop image shows through
            self.flowchart_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            # Fixed vertical policy: flowchart stays at its minimum height
            # and does not grow into the debug overlay zone.
            from PySide6.QtWidgets import QSizePolicy
            _fsp = self.flowchart_widget.sizePolicy()
            _fsp.setVerticalPolicy(QSizePolicy.Policy.Fixed)
            self.flowchart_widget.setSizePolicy(_fsp)
            self.main_layout.addWidget(self.flowchart_widget)
            try:
                self.logger.info('gui', 'Flowchart widget initialized')
            except Exception:
                pass
        except Exception as e:
            # Fallback to placeholder if FlowchartWidget fails
            try:
                self.logger.error('gui', f'Failed to create FlowchartWidget: {e}')
            except Exception:
                print(f'ERROR: Failed to create FlowchartWidget: {e}')
            
            self.flowchart_container = QWidget(self)
            self.flowchart_container.setObjectName('flowchart_container')
            self.flowchart_container.setLayout(QVBoxLayout())
            self.flowchart_container.setAttribute(Qt.WA_TranslucentBackground, True)
            
            placeholder = QLabel('Flowchart/Pipeline visualization unavailable', self.flowchart_container)
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet('color: #666; font-size: 14px; padding: 40px; background: transparent;')
            self.flowchart_container.layout().addWidget(placeholder)
            self.main_layout.addWidget(self.flowchart_container)

    def init_debug_terminal(self):
        cw = self.centralWidget() or self
        self.debug_terminal_container = QWidget(cw)
        self.debug_terminal_container.setObjectName('debug_terminal_container')
        self.debug_terminal_container.setLayout(QVBoxLayout())
        self.debug_terminal_container.setStyleSheet(
            '#debug_terminal_container { background: #111; border-top: 1px solid #333; }'
        )
        # create a QTextEdit debug log area and expose via register_debug_terminal
        try:
            from PySide6.QtWidgets import QTextEdit
            self.debug_log = QTextEdit(self.debug_terminal_container)
            self.debug_log.setReadOnly(True)
            self.debug_log.setMinimumHeight(80)
            self.debug_log.setStyleSheet(
                'QTextEdit { background-color: #000000; color: #4FC3FF;'
                ' border: none; font-family: Consolas, "Courier New", monospace; font-size: 11px; }'
            )
            self.debug_terminal_container.layout().addWidget(self.debug_log)
            # register for use by controller/connector
            self.register_debug_terminal(self.debug_log)
        except Exception:
            self.debug_log = None
        # Float at the bottom — does NOT live in main_layout so flowchart is undisturbed
        self._position_debug_overlay()
        self.debug_terminal_container.setVisible(False)
        self.debug_terminal_container.raise_()

    def init_settings_panel(self):
        # instantiate a default SettingsWindow if one is not present (add-only)
        print("DEBUG: init_settings_panel() called")
        if getattr(self, 'settings_panel', None) is None:
            print("DEBUG: settings_panel is None, creating new one")
            try:
                print("DEBUG: importing SettingsWindow")
                from bspg.gui.settings_panel.settings_window import SettingsWindow
                print("DEBUG: SettingsWindow imported successfully")
                print(f"DEBUG: controller = {getattr(self, 'controller', None)}")
                print(f"DEBUG: parent = {self}")
                self.settings_panel = SettingsWindow(controller=getattr(self, 'controller', None), parent=self)
                print(f"DEBUG: SettingsWindow created: {self.settings_panel}")
                # ensure it's added to the main layout but hidden by default so main window appears normally
                self.settings_panel.setVisible(False)
                print("DEBUG: settings_panel.setVisible(False) called")
                # Add with stretch factor so it takes remaining space when visible
                self.main_layout.addWidget(self.settings_panel, stretch=2)
                print("DEBUG: settings_panel added to main_layout with stretch=2")
            except Exception as e:
                # FIX: Log exceptions instead of silently swallowing
                print(f'ERROR: Failed to initialize settings panel: {e}')
                import traceback
                traceback.print_exc()
                try:
                    self.logger.error('gui', f'Failed to initialize settings panel: {e}')
                except Exception:
                    pass
                self.settings_panel = None
        else:
            print(f"DEBUG: settings_panel already exists: {self.settings_panel}")

    def load_assets(self):
        # placeholder for future asset loading
        return

    def load_logo(self):
        """Load the BSPG logo pixmap. Actual logic added in E-7."""
        return

    def apply_logo_styles(self):
        """Apply any logo-specific styling. Existing QSS must not be modified."""
        return

    def load_backdrop(self):
        """Load and set the backdrop/background image for the central widget."""
        try:
            import os
            
            # Look for backdrop image in hqspg/assets
            root = os.path.dirname(os.path.abspath(__file__))
            # Go up from bspg/bspg/gui to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(root)))
            backdrop_path = os.path.join(project_root, 'hqspg', 'assets', 'BHQSPGBackdrop.png')
            
            if os.path.exists(backdrop_path):
                # Normalize path for QSS (use forward slashes even on Windows)
                backdrop_path = backdrop_path.replace('\\', '/')
                
                # Set backdrop as central widget background via inline stylesheet
                # This allows widgets with transparent backgrounds to show the image behind them
                current_style = self.central_widget.styleSheet()
                backdrop_style = f"""
                    QWidget#CentralWidget {{
                        background-image: url({backdrop_path});
                        background-repeat: no-repeat;
                        background-position: center top;
                        background-color: #111;
                    }}
                """
                self.central_widget.setStyleSheet(current_style + backdrop_style)
                
                self.logger.info('gui', f'Backdrop set as background from {backdrop_path}')
            else:
                self.logger.info('gui', f'Backdrop image not found at {backdrop_path}')
        except Exception as e:
            self.logger.warning('gui', f'Failed to load backdrop: {e}')
            import traceback
            traceback.print_exc()

    # --- F-7 integration helpers (add-only) ---
    def init_controller(self):
        """Initialize GUIController. Add-only; do not modify existing GUI."""
        if hasattr(self, 'controller'):
            return

        try:
            from bspg.gui.logic.gui_controller import GUIController
            print("DEBUG: Creating GUIController...")
            self.controller = GUIController(
                main_window=self,
                app_config=self.app_config,
                logger=self.logger,
            )
            print(f"DEBUG: GUIController created: {self.controller}")
        except Exception as e:
            print(f"DEBUG: Failed to create GUIController: {e}")
            import traceback
            traceback.print_exc()
            self.controller = None
        # If settings panel was created earlier, inject the controller reference
        try:
            if hasattr(self, 'settings_panel') and self.settings_panel is not None and self.controller is not None:
                try:
                    # set controller reference on panel and sync config
                    if hasattr(self.settings_panel, '__dict__'):
                        self.settings_panel.controller = self.controller
                    try:
                        self.controller.sync_config_to_settings()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def get_controller(self):
        return getattr(self, 'controller', None)

    def register_flowchart(self, widget):
        self.flowchart_widget = widget

    def register_debug_terminal(self, widget):
        self.debug_terminal_widget = widget
        # Wire the widget into the logger's router so output actually appears
        try:
            from bspg.gui.debug_terminal.adapter import DebugTerminalSinkAdapter
            from bspg.core.logging import bspg_logger
            sink = DebugTerminalSinkAdapter(widget)
            bspg_logger.router.add_sink(sink)
            self._debug_sink = sink  # keep a reference so it isn't GC'd
        except Exception:
            pass

    def register_settings_panel(self, widget):
        self.settings_panel = widget

    def register_top_lanes(self, run_lane=None, fileio_lane=None):
        if run_lane is not None:
            self.top_lane_run = run_lane
        if fileio_lane is not None:
            self.top_lane_fileio = fileio_lane

    def system_ready(self):
        """Called after all widgets are constructed. Add-only."""
        try:
            if hasattr(self, 'controller') and self.controller is not None:
                try:
                    self.controller.sync_config_to_settings()
                except Exception:
                    pass
                try:
                    self.controller.reset_pipeline_status()
                except Exception:
                    pass
                # Gate run button on legal acceptance now that all widgets exist
                try:
                    self.controller.check_terms_gate()
                except Exception:
                    pass
                self.logger.info('gui', 'System ready.')
                # ensure HRT beacon defaults to red until link succeeds
                try:
                    if hasattr(self, 'set_hrt_beacon_red'):
                        try:
                            self.set_hrt_beacon_red()
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    def apply_terms_overlay(self):
        """
        Applies a transparent overlay that blocks interaction but keeps the GUI visible.
        Only the Settings button should remain visually active (pulsing).
        """
        try:
            if hasattr(self, "_terms_overlay") and self._terms_overlay is not None:
                try:
                    self._terms_overlay.show()
                    return
                except Exception:
                    pass
        except Exception:
            pass

        try:
            # Delay actual creation until after layout is complete so geometry is correct
            QTimer.singleShot(0, self._apply_terms_overlay_real)
        except Exception:
            pass

    def _apply_terms_overlay_real(self):
        try:
            # Parent to central widget so the window frame remains visible
            parent = self.centralWidget() or self
            overlay = QWidget(parent)
            overlay.setObjectName("termsOverlay")
            overlay.setStyleSheet("""
                QWidget#termsOverlay {
                    background-color: rgba(0, 0, 0, 120);
                }
            """)
            # Size to the central widget BUT exclude the top button area
            # Top lane is ~130px tall, start overlay below it
            try:
                w = parent.width()
                h = parent.height()
                button_area_height = 130  # Height of top lane container
                overlay.setGeometry(0, button_area_height, max(0, w), max(0, h - button_area_height))
            except Exception:
                try:
                    overlay.setGeometry(self.rect())
                except Exception:
                    pass
            overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            overlay.raise_()
            overlay.show()

            self._terms_overlay = overlay
        except Exception:
            pass

    def remove_terms_overlay(self):
        try:
            if hasattr(self, "_terms_overlay") and self._terms_overlay is not None:
                try:
                    self._terms_overlay.hide()
                    try:
                        self._terms_overlay.deleteLater()
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    self._terms_overlay = None
                except Exception:
                    pass

            # Stop title warning and restore original title
            try:
                self.stop_terms_warning_banner()
            except Exception:
                pass
        except Exception:
            pass

    def _position_debug_overlay(self):
        """Pin the debug overlay to the bottom of the central widget."""
        try:
            cw = self.centralWidget() or self
            panel = self.debug_terminal_container
            panel_h = getattr(self, '_DEBUG_OVERLAY_H', 200)
            panel.setGeometry(0, cw.height() - panel_h, cw.width(), panel_h)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # apply rounded corner mask
        try:
            bmp = QBitmap(self.size())
            bmp.fill(Qt.GlobalColor.color0)
            p = QPainter(bmp)
            p.setBrush(Qt.GlobalColor.color1)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(bmp.rect(), 18, 18)
            p.end()
            self.setMask(bmp)
        except Exception:
            pass
        # reposition floating debug overlay
        try:
            if hasattr(self, 'debug_terminal_container') and self.debug_terminal_container is not None:
                self._position_debug_overlay()
        except Exception:
            pass
        # reposition terms overlay if present
        try:
            if hasattr(self, "_terms_overlay") and self._terms_overlay is not None:
                try:
                    parent = self.centralWidget() or self
                    try:
                        self._terms_overlay.setGeometry(parent.rect())
                    except Exception:
                        self._terms_overlay.setGeometry(self.rect())
                except Exception:
                    pass
        except Exception:
            pass

    # --- Module H view helpers (add-only) ---
    def show_terms_required_modal(self):
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Terms Required",
                "You must accept the legal terms before using HQSPG.\n"
                "Please review them in Settings → Legal & Responsible Use."
            )
        except Exception:
            pass

    def show_terms_banner(self):
        """Show a persistent flashing banner and start pulsing the Settings button."""
        try:
            if self.terms_banner is None:
                return
            self.terms_banner.setText('Accept legal terms first')
            # Reset height limit to allow banner to display
            self.terms_banner.setMaximumHeight(50)
            self.terms_banner.setVisible(True)

            # Start flashing (toggle visibility/style)
            if self._terms_banner_timer is None:
                try:
                    self._terms_banner_timer = QTimer(self)
                    self._terms_banner_timer.setInterval(600)
                    def _toggle():
                        try:
                            cur = self.terms_banner.styleSheet()
                            if 'background-color: red' in cur:
                                self.terms_banner.setStyleSheet('color: white; background-color: none; padding: 6px;')
                            else:
                                self.terms_banner.setStyleSheet('color: white; background-color: red; padding: 6px;')
                        except Exception:
                            pass
                    self._terms_banner_timer.timeout.connect(_toggle)
                    self._terms_banner_timer.start()
                except Exception:
                    pass

            # start pulsing settings button if available
            try:
                self.start_pulse_settings_button()
            except Exception:
                pass
        except Exception:
            pass

    def show_terms_warning_banner(self):
        """Flash a red warning in the title bar (soft warning)."""
        try:
            # toggle window title between original and warning text
            warning = "HQSPG — Accept legal terms first ⚠️"
            if not hasattr(self, '_title_warn_timer') or self._title_warn_timer is None:
                try:
                    self._title_warn_timer = QTimer(self)
                    self._title_warn_timer.setInterval(600)
                    def _toggle_title():
                        try:
                            cur = self.windowTitle()
                            if cur == warning:
                                self.setWindowTitle(self._original_title)
                            else:
                                self.setWindowTitle(warning)
                        except Exception:
                            pass
                    self._title_warn_timer.timeout.connect(_toggle_title)
                    self._title_warn_timer.start()
                except Exception:
                    pass
        except Exception:
            pass

    def stop_terms_warning_banner(self):
        try:
            if hasattr(self, '_title_warn_timer') and self._title_warn_timer is not None:
                try:
                    self._title_warn_timer.stop()
                    self._title_warn_timer.deleteLater()
                except Exception:
                    pass
                self._title_warn_timer = None
            try:
                self.setWindowTitle(self._original_title)
            except Exception:
                pass
        except Exception:
            pass

    def stop_terms_banner(self):
        try:
            if self.terms_banner is not None:
                self.terms_banner.setVisible(False)
            if self._terms_banner_timer is not None:
                try:
                    self._terms_banner_timer.stop()
                    self._terms_banner_timer.deleteLater()
                except Exception:
                    pass
                self._terms_banner_timer = None
            try:
                self.stop_pulse_settings_button()
            except Exception:
                pass
        except Exception:
            pass

    def disable_all_features_except_settings(self):
        """Non-destructive lockout: show overlay + pulse settings button + title warning."""
        try:
            # apply a soft overlay that blocks interaction but keeps UI visible
            try:
                self.apply_terms_overlay()
            except Exception:
                pass

            # pulse settings button if present so user can accept terms
            try:
                if hasattr(self, "top_lane_run") and hasattr(self.top_lane_run, "settings_button"):
                    try:
                        self.pulse_settings_button()
                    except Exception:
                        pass
            except Exception:
                pass

            # start title warning
            try:
                self.show_terms_warning_banner()
            except Exception:
                pass
        except Exception:
            pass
        # --- HARD OVERRIDE: GUI MUST REMAIN VISIBLE (no destructive disables) ---
        try:
                self.setEnabled(True)
        except Exception:
            pass

            cw = self.centralWidget()
            self.setEnabled(True)
            if cw:
                try:
                    cw.setEnabled(True)
                except Exception:
                    pass
                try:
                    for child in cw.findChildren(QWidget):
                        try:
                            child.setEnabled(True)
                        except Exception:
                            pass
                except Exception:
                    pass
            # Ensure we have a list of interactive widgets; build if missing
            try:
                if not hasattr(self, 'all_interactive_widgets') or not getattr(self, 'all_interactive_widgets'):
                    try:
                        interactive_types = (
                            QAbstractButton,
                            QAbstractSpinBox,
                            QSlider,
                            QComboBox,
                            QLineEdit,
                            QTextEdit,
                            QPlainTextEdit,
                            QCheckBox,
                            QRadioButton,
                            QTabWidget,
                        )
                        widgets = []
                        for w in self.findChildren(QWidget):
                            if w is self or w is self.central_widget:
                                continue
                            if isinstance(w, interactive_types):
                                widgets.append(w)
                        self.all_interactive_widgets = widgets
                    except Exception:
                        self.all_interactive_widgets = []
            except Exception:
                pass

            # Re-disable only interactive widgets (except Settings)
            try:
                settings_btn = getattr(self, 'settings_button', None)
                for widget in getattr(self, 'all_interactive_widgets', []):
                    try:
                        if widget is not settings_btn:
                            widget.setEnabled(False)
                    except Exception:
                        pass
            except Exception:
                pass

            # Ensure Settings button is enabled and pulsing
            try:
                if hasattr(self, 'settings_button') and self.settings_button is not None:
                    try:
                        self.settings_button.setEnabled(True)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self.pulse_settings_button()
            except Exception:
                pass
        except Exception:
            pass

    def navigate_to_legal_settings(self):
        """Open or focus the settings panel and scroll to legal section."""
        try:
            if hasattr(self, 'settings_panel') and self.settings_panel is not None:
                try:
                    self.settings_panel.setVisible(True)
                    if hasattr(self.settings_panel, 'scroll_to_legal_section'):
                        try:
                            self.settings_panel.scroll_to_legal_section()
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    # --- Module I: HRT beacon helpers (add-only) ---
    def set_hrt_beacon_green(self):
        """Mark HRT beacon as green if present."""
        try:
            fileio = getattr(self, 'top_lane_fileio', None)
            if fileio is None:
                return
            if hasattr(fileio, 'hrt_beacon_label') and fileio.hrt_beacon_label is not None:
                try:
                    fileio.hrt_beacon_label.setText('HRT: Connected')
                    fileio.hrt_beacon_label.setStyleSheet(
                        'background-color: #4FC3FF; color: #000000;'
                        ' border: 1px solid #000000; border-radius: 6px; padding: 4px;'
                    )
                    try:
                        fileio.hrt_beacon_label.setToolTip(
                            "Hot Rod Tuner Link Status\n\n"
                            "● Blue — HQSPG is linked to Hot Rod Tuner.\n"
                            "   If your system overheats, Hot Rod Tuner may safely close HQSPG.\n\n"
                            "○ Purple — Not linked.\n"
                            "   HQSPG will run normally, and Hot Rod Tuner will not manage it.\n\n"
                            "Linking is optional. Hot Rod Tuner is a separate safety app that "
                            "monitors your system and can close connected apps to protect hardware."
                        )
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def set_hrt_beacon_red(self):
        """Ensure HRT beacon shows not-linked state."""
        try:
            fileio = getattr(self, 'top_lane_fileio', None)
            if fileio is None:
                return
            if hasattr(fileio, 'hrt_beacon_label') and fileio.hrt_beacon_label is not None:
                try:
                    fileio.hrt_beacon_label.setText('HRT: Not linked')
                    fileio.hrt_beacon_label.setStyleSheet(
                        'background-color: #9040C8; color: #000000;'
                        ' border: 1px solid #000000; border-radius: 6px; padding: 4px;'
                    )
                    try:
                        fileio.hrt_beacon_label.setToolTip(
                            "Hot Rod Tuner Link Status\n\n"
                            "● Blue — HQSPG is linked to Hot Rod Tuner.\n"
                            "   If your system overheats, Hot Rod Tuner may safely close HQSPG.\n\n"
                            "○ Purple — Not linked.\n"
                            "   HQSPG will run normally, and Hot Rod Tuner will not manage it.\n\n"
                            "Linking is optional. Hot Rod Tuner is a separate safety app that "
                            "monitors your system and can close connected apps to protect hardware."
                        )
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def enable_all_features(self):
        """
        Disables only interactive widgets, not the entire window.
        The GUI must remain fully visible.
        """
        # Determine the settings button if available
        settings_btn = getattr(self, 'settings_button', None)
        if settings_btn is None:
            try:
                if hasattr(self, 'top_lane_run') and hasattr(self.top_lane_run, 'settings_button'):
                    settings_btn = self.top_lane_run.settings_button
                    # expose a consistent attribute for other code paths
                    self.settings_button = settings_btn
            except Exception:
                settings_btn = None

        # Build or refresh cached list of interactive widgets
        try:
            interactive_types = (
                QAbstractButton,
                QAbstractSpinBox,
                QSlider,
                QComboBox,
                QLineEdit,
                QTextEdit,
                QPlainTextEdit,
                QCheckBox,
                QRadioButton,
                QTabWidget,
            )
            widgets = []
            for w in self.findChildren(QWidget):
                # skip main window and central widget explicitly
                if w is self or w is self.central_widget:
                    continue
                # skip known container widgets
                if w in (getattr(self, 'top_lane_container', None),
                         getattr(self, 'logo_container', None),
                         getattr(self, 'flowchart_container', None),
                         getattr(self, 'debug_terminal_container', None),
                         getattr(self, 'settings_panel', None)):
                    continue
                # include only interactive types
                try:
                    if isinstance(w, interactive_types):
                        widgets.append(w)
                except Exception:
                    pass

            # cache for future use
            self.all_interactive_widgets = widgets

            # Disable interactive widgets except the Settings button
            for widget in self.all_interactive_widgets:
                try:
                    if widget is not settings_btn:
                        widget.setEnabled(False)
                except Exception:
                    pass

        except Exception:
            # worst-case: do not disable anything to avoid breaking UI
            return

        # Make sure the main window and central widget stay enabled and visible
        try:
            self.setEnabled(True)
        except Exception:
            pass
        try:
            if self.centralWidget():
                self.centralWidget().setEnabled(True)
        except Exception:
            pass

        # Pulse the settings button and show title warning
        try:
            if settings_btn is not None:
                try:
                    settings_btn.setEnabled(True)
                except Exception:
                    pass
            self.pulse_settings_button()
            self.show_terms_warning_banner()
        except Exception:
            pass
    def start_pulse_settings_button(self):
        try:
            if self._settings_pulse_timer is not None:
                return
            btn = None
            try:
                if hasattr(self, 'top_lane_run') and hasattr(self.top_lane_run, 'settings_button'):
                    btn = self.top_lane_run.settings_button
            except Exception:
                pass
            if btn is None:
                return

            self._settings_pulse_timer = QTimer(self)
            self._settings_pulse_timer.setInterval(500)
            def _pulse():
                try:
                    cur = btn.styleSheet()
                    if 'background-color: red' in cur:
                        btn.setStyleSheet('')
                    else:
                        btn.setStyleSheet('background-color: red; color: white;')
                except Exception:
                    pass
            self._settings_pulse_timer.timeout.connect(_pulse)
            self._settings_pulse_timer.start()
        except Exception:
            pass

    def stop_pulse_settings_button(self):
        try:
            if self._settings_pulse_timer is not None:
                try:
                    self._settings_pulse_timer.stop()
                    self._settings_pulse_timer.deleteLater()
                except Exception:
                    pass
                self._settings_pulse_timer = None
            try:
                if hasattr(self, 'top_lane_run') and hasattr(self.top_lane_run, 'settings_button'):
                    try:
                        self.top_lane_run.settings_button.setStyleSheet('')
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def log_debug_message(self, msg: str):
        """Append a timestamped debug message to the GUI debug log or logger."""
        try:
            text = str(msg)
        except Exception:
            try:
                text = repr(msg)
            except Exception:
                text = '<unprintable debug message>'

        try:
            timestamp = QDateTime.currentDateTime().toString('HH:mm:ss')
        except Exception:
            timestamp = ''

        line = f'[{timestamp}] {text}' if timestamp else text

        try:
            widget = getattr(self, 'debug_terminal_widget', None) or getattr(self, 'debug_log', None)
            if widget is not None:
                try:
                    if hasattr(widget, 'appendPlainText'):
                        widget.appendPlainText(line)
                    elif hasattr(widget, 'append'):
                        widget.append(line)
                    else:
                        try:
                            cur = widget.toPlainText()
                            widget.setPlainText(cur + '\n' + line)
                        except Exception:
                            pass
                    return
                except Exception:
                    pass
        except Exception:
            pass

        # Fallback to logger
        try:
            if hasattr(self, 'logger') and self.logger is not None:
                try:
                    self.logger.info('debug', line)
                except Exception:
                    pass
        except Exception:
            pass

    def show_toast(self, message: str, duration_ms: int = 2500):
        """Shows a transient toast message overlay in bottom-right corner."""
        try:
            toast = QLabel(message, self)
            toast.setStyleSheet("""
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 11px;
            """)
            toast.adjustSize()

            # Position bottom-right
            try:
                x = max(10, self.width() - toast.width() - 20)
                y = max(10, self.height() - toast.height() - 20)
                toast.move(x, y)
            except Exception:
                pass
            toast.setWindowFlag(Qt.ToolTip)
            toast.show()
            try:
                QTimer.singleShot(int(duration_ms), toast.deleteLater)
            except Exception:
                pass
        except Exception:
            pass

    def update_hrt_status_ui(self):
        try:
            if hasattr(self, 'settings_panel') and self.settings_panel is not None and hasattr(self.settings_panel, 'refresh_hrt_status'):
                try:
                    self.settings_panel.refresh_hrt_status()
                except Exception:
                    pass
        except Exception:
            pass
