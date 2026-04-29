from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox
from PySide6.QtCore import Signal


class SettingsPanel(QWidget):
    # expose only the minimal controls required by product vision
    backsplash_toggled = Signal(bool)
    hover_toggled = Signal(bool)
    hotrod_link_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setObjectName('SettingsPanel')
        self._build()

    def _build(self):
        # Keep the panel simple and readable
        self.setStyleSheet('''
            QWidget#SettingsPanel { background-color: #f0f0f0; color: #111; }
            QWidget#SettingsPanel QPushButton { color: #111; background: rgba(240,240,240,0.95); border: 1px solid rgba(0,0,0,0.08); }
            QWidget#SettingsPanel QLabel { color: #111; }
            QWidget#SettingsPanel QCheckBox { color: #111; }
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel('Settings'))

        # Backplash toggle (on/off)
        self.backsplash_chk = QCheckBox('Backsplash Off')
        self.backsplash_chk.setObjectName('BacksplashToggle')
        self.backsplash_chk.stateChanged.connect(lambda s: self.backsplash_toggled.emit(bool(s)))

        # Hover logic toggle (on/off)
        self.hover_chk = QCheckBox('Hover Logic On')
        self.hover_chk.setObjectName('HoverLogicToggle')
        self.hover_chk.stateChanged.connect(lambda s: self.hover_toggled.emit(bool(s)))

        # Manual link to Hot Rod Tuner (opens connector in advanced panel)
        self.hotrod_btn = QPushButton('Manually link to Hot Rod Tuner')
        self.hotrod_btn.setObjectName('HotRodLinkBtn')
        self.hotrod_btn.clicked.connect(lambda: self.hotrod_link_clicked.emit())

        layout.addWidget(self.backsplash_chk)
        layout.addWidget(self.hover_chk)
        layout.addWidget(self.hotrod_btn)
