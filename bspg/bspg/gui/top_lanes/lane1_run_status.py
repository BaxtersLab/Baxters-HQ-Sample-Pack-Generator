from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

from bspg.core.config import AppConfig
from bspg.core.logging import bspg_logger


class TopLaneRunStatus(QWidget):
    def __init__(self, parent=None, app_config=None):
        super().__init__(parent)
        # Make background transparent so backdrop image shows through
        # Use attribute instead of stylesheet to avoid overriding button styles
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # prefer injected AppConfig; fallback for tests
        try:
            if app_config is not None:
                self.app_config = app_config
            else:
                self.app_config = AppConfig()
        except Exception:
            self.app_config = AppConfig()
        self.logger = bspg_logger

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(12, 12, 12, 12)

        self.run_button = QPushButton('Run', self)
        self.run_button.setMinimumWidth(100)

        self.status_label = QLabel('Idle', self)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setSizePolicy(self.status_label.sizePolicy().horizontalPolicy(),
                                        self.status_label.sizePolicy().verticalPolicy())

        self.settings_button = QPushButton('Settings', self)
        self.debug_button = QPushButton('Debug', self)

        self.layout.addWidget(self.run_button)
        self.layout.addWidget(self.status_label, 1)
        self.layout.addWidget(self.settings_button)
        self.layout.addWidget(self.debug_button)

    def update_status(self, text: str):
        self.status_label.setText(text)

    def apply_styles(self):
        # placeholder for black-outline styling
        return

    def load_icons(self):
        # placeholder for icon loading
        return
from PySide6.QtWidgets import QWidget

class Lane1RunStatus(QWidget):
    pass
