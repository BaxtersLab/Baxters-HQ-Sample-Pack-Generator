import os
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from bspg.core.config import AppConfig
from bspg.core.logging import bspg_logger


class TopLaneFileIO(QWidget):
    def __init__(self, parent=None, app_config=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        try:
            if app_config is not None:
                self.app_config = app_config
            else:
                self.app_config = AppConfig()
        except Exception:
            self.app_config = AppConfig()
        self.logger = bspg_logger

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(12, 8, 12, 8)

        # Input file(s) button — auto-sized to text
        self.input_button = QPushButton('Input File(s)', self)
        self.input_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.input_button)

        layout.addSpacing(8)   # 2 spaces

        # Input display box — 20 chars wide, light gray
        self.input_display = QLabel('', self)
        self.input_display.setObjectName('FileIODisplay')
        self.input_display.setFixedWidth(160)
        self.input_display.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.input_display)

        layout.addSpacing(32)  # 4 spaces gap between the two pairs

        # Output folder button — auto-sized to text
        self.output_button = QPushButton('Output Folder', self)
        self.output_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.output_button)

        layout.addSpacing(8)   # 2 spaces

        # Output display box — 20 chars wide, light gray
        self.output_display = QLabel('', self)
        self.output_display.setObjectName('FileIODisplay')
        self.output_display.setFixedWidth(160)
        self.output_display.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.output_display)

        layout.addStretch()

        # Thermometer icon — 40px, sits just left of HRT indicator
        self.thermometer_label = QLabel('\U0001f321', self)
        self.thermometer_label.setObjectName('ThermometerIcon')
        self.thermometer_label.setAlignment(Qt.AlignCenter)
        tf = QFont()
        tf.setPixelSize(28)
        self.thermometer_label.setFont(tf)
        self.thermometer_label.setFixedSize(40, 40)
        layout.addWidget(self.thermometer_label)

        # HRT link indicator
        self.hrt_beacon_label = QLabel('HRT: Unknown', self)
        self.hrt_beacon_label.setObjectName('HRTBeacon')
        self.hrt_beacon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hrt_beacon_label)

    # ------------------------------------------------------------------
    def set_input_files_display(self, files):
        """Show abbreviated file stems (first 5 chars each) in input box."""
        try:
            if not files:
                self.input_display.setText('')
                return
            names = [os.path.splitext(os.path.basename(f))[0][:5] for f in files]
            self.input_display.setText(', '.join(names))
        except Exception:
            pass

    def set_output_folder_display(self, folder):
        """Show folder name (up to 20 chars) in output box."""
        try:
            if not folder:
                self.output_display.setText('')
                return
            name = os.path.basename(folder.rstrip('/\\')) or folder
            self.output_display.setText(name[:20])
        except Exception:
            pass

    def update_thermometer(self, value: float):
        return

    def update_hrt_status(self, connected: bool):
        return

    def apply_styles(self):
        return

    def load_icons(self):
        return


from PySide6.QtWidgets import QWidget

class Lane2FileIO(QWidget):
    pass
