from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QLabel, QProgressBar, QDoubleSpinBox
from PySide6.QtCore import Signal, Qt, QPoint
from hqspg._version import __product_name__


class CustomTitleBar(QWidget):
    """A simple custom title bar for frameless windows.

    Provides app name, drag-to-move, minimize and close buttons.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mouse_pos = None
        self._win_pos = None
        self.setObjectName('CustomTitleBar')
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        # ensure stylesheet background is painted
        try:
            self.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass
        self.app_label = QLabel(__product_name__)
        self.app_label.setObjectName('TitleBarAppName')

        self.btn_min = QPushButton('—')
        self.btn_min.setObjectName('TitleBarMin')
        self.btn_min.setFixedSize(28, 22)
        self.btn_min.clicked.connect(lambda: self.window().showMinimized())

        self.btn_close = QPushButton('✕')
        self.btn_close.setObjectName('TitleBarClose')
        self.btn_close.setFixedSize(28, 22)
        self.btn_close.clicked.connect(lambda: self.window().close())

        layout.addWidget(self.app_label)
        layout.addStretch(1)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_close)

        # make titlebar a consistent height
        self.setFixedHeight(36)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mouse_pos = event.globalPos()
            self._win_pos = self.window().pos()

    def mouseMoveEvent(self, event):
        if self._mouse_pos is not None:
            delta = event.globalPos() - self._mouse_pos
            self.window().move(self._win_pos + delta)

    def mouseReleaseEvent(self, event):
        self._mouse_pos = None
        self._win_pos = None



class TopBar(QWidget):
    settings_toggled = Signal(bool)
    load_clicked = Signal()
    save_clicked = Signal()
    # mode selection removed (no functional difference between previous options)
    debug_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.setObjectName('TopBar')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Backplash toggle moved into SettingsPanel (keep settings_toggled signal
        # for compatibility, but TopBar no longer contains the checkbox)

        # Note: load/save moved to a dedicated Settings panel to reduce clutter

        # extractor controls
        self.silence_spin = QDoubleSpinBox()
        self.silence_spin.setRange(0.0, 1.0)
        self.silence_spin.setSingleStep(0.01)
        self.silence_spin.setValue(0.01)
        self.silence_spin.setSuffix(' silence')

        self.transient_spin = QDoubleSpinBox()
        self.transient_spin.setRange(0.1, 10.0)
        self.transient_spin.setSingleStep(0.1)
        self.transient_spin.setValue(1.5)
        self.transient_spin.setSuffix(' transient')

        # small indicator
        self.indicator = QLabel('●')
        self.indicator.setObjectName('Indicator')
        self.indicator.setAlignment(Qt.AlignCenter)

        # Debug terminal toggle
        self.debug_toggle_btn = QPushButton('Debug Terminal')
        self.debug_toggle_btn.setObjectName('DebugToggle')
        self.debug_toggle_btn.clicked.connect(lambda: self.debug_toggled.emit())

        # Demo logs removed (was used for simulated logs during development)
        layout.addWidget(self.silence_spin)
        layout.addWidget(self.transient_spin)
        layout.addStretch(1)
        layout.addWidget(self.indicator)
        # place debug toggle at the far right of the top bar
        layout.addWidget(self.debug_toggle_btn)


class BottomBar(QWidget):
    generate = Signal()
    export = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.setObjectName('BottomBar')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # action buttons relocated to SettingsPanel; provide single Settings button
        self.settings_btn = QPushButton('Settings')
        self.settings_btn.setObjectName('SettingsBtn')

        self.generate_btn = QPushButton('Generate')
        self.generate_btn.clicked.connect(lambda: self.generate.emit())
        # Randomize removed — not used in this application

        self.export_btn = QPushButton('Export')
        self.export_btn.clicked.connect(lambda: self.export.emit())

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        # left: progress; right: settings
        layout.addWidget(self.generate_btn)
        layout.addStretch(1)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.settings_btn)
