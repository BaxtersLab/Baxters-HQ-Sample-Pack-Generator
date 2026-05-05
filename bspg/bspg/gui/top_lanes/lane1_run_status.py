from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt

from bspg.core.config import AppConfig
from bspg.core.logging import bspg_logger


class TopLaneRunStatus(QWidget):
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
        layout.setSpacing(8)
        layout.setContentsMargins(12, 8, 12, 8)

        # Run button
        self.run_button = QPushButton('Run', self)
        self.run_button.setObjectName('RunButton')
        self.run_button.setFixedHeight(32)
        self.run_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.run_button)

        # Status pill label
        self.status_label = QLabel('Idle', self)
        self.status_label.setObjectName('StatusPill')
        self.status_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.status_label.setFixedHeight(26)
        self.status_label.setMinimumWidth(80)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName('PipelineProgress')
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('%p%')
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.progress_bar, 1)

        # Settings / Debug
        self.settings_button = QPushButton('Settings', self)
        self.debug_button = QPushButton('Debug', self)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.debug_button)

    # Map internal pipeline stage names → short display labels
    _STAGE_LABELS = {
        'IDLE': 'Idle',
        'STEM_SEPARATION': 'Separating',
        'STEM_REPAIR': 'Repairing',
        'SAMPLE_CHOP': 'Chopping',
        'FINALIZING': 'Finalizing',
        'COMPLETE': 'Done',
        'ERROR': 'Error',
    }

    def update_status(self, text: str):
        display = self._STAGE_LABELS.get(str(text).strip(), str(text))
        self.status_label.setText(display)
        # Colour the pill based on state keyword
        t = display.lower()
        if any(k in t for k in ('done', 'complete', 'finish', 'success')):
            self.status_label.setStyleSheet(
                'QLabel#StatusPill { background:#4FC3FF; color:#000; border:1px solid #000;'
                ' border-radius:6px; padding:2px 8px; font-weight:700; font-size:11px; }'
            )
        elif any(k in t for k in ('error', 'fail', 'abort')):
            self.status_label.setStyleSheet(
                'QLabel#StatusPill { background:#9040C8; color:#000; border:1px solid #000;'
                ' border-radius:6px; padding:2px 8px; font-weight:700; font-size:11px; }'
            )
        elif any(k in t for k in ('run', 'start', 'process', 'stage', 'separ', 'repair', 'chop')):
            self.status_label.setStyleSheet(
                'QLabel#StatusPill { background:#F0A500; color:#000; border:1px solid #000;'
                ' border-radius:6px; padding:2px 8px; font-weight:700; font-size:11px; }'
            )
        else:
            self.status_label.setStyleSheet('')  # falls back to QSS default

    def update_progress(self, value: float):
        """Set progress bar 0.0-1.0 or 0-100."""
        try:
            v = int(value * 100) if value <= 1.0 else int(value)
            self.progress_bar.setValue(max(0, min(100, v)))
        except Exception:
            pass

    def reset_progress(self):
        self.progress_bar.setValue(0)
        self.status_label.setText('Idle')
        self.status_label.setStyleSheet('')

    def apply_styles(self):
        return

    def load_icons(self):
        return


from PySide6.QtWidgets import QWidget

class Lane1RunStatus(QWidget):
    pass
