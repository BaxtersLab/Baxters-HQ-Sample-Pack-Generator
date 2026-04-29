from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

from bspg.core.config import AppConfig
from bspg.core.logging import bspg_logger


class TopLaneFileIO(QWidget):
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

        self.input_button = QPushButton('Input File(s)', self)
        self.input_button.setMinimumWidth(120)

        self.output_button = QPushButton('Output Folder', self)
        self.output_button.setMinimumWidth(120)

        self.thermometer_label = QLabel('Thermometer', self)
        self.thermometer_label.setAlignment(Qt.AlignCenter)

        self.hrt_beacon_label = QLabel('HRT: Unknown', self)
        self.hrt_beacon_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.input_button)
        self.layout.addWidget(self.output_button)
        self.layout.addWidget(self.thermometer_label)
        self.layout.addWidget(self.hrt_beacon_label)

    def update_thermometer(self, value: float):
        # placeholder for updating thermometer display
        return

    def update_hrt_status(self, connected: bool):
        # placeholder for updating HRT beacon
        return

    def apply_styles(self):
        # placeholder for styling
        return

    def load_icons(self):
        # placeholder for loading icons
        return
from PySide6.QtWidgets import QWidget

class Lane2FileIO(QWidget):
    pass
