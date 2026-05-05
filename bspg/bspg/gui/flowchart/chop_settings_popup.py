from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QSpinBox, QPushButton, QWidget
)
from PySide6.QtCore import Qt


class ChopSettingsPopup(QDialog):
    """
    Lavender gear-button popup for Sample Chop adjustments.

    Controls:
        silence_threshold    — RMS level below which audio is treated as silence
        transient_sensitivity — multiplier for transient detection peaks
        pre_ms               — milliseconds of audio to include before a detected onset
        post_ms              — milliseconds of audio to include after a detected onset
        min_slice_ms         — shortest allowed slice (shorter ones are discarded)
        max_slice_ms         — longest allowed slice (longer ones are split)
    """

    def __init__(self, app_config=None, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self.setWindowTitle("Sample Chop Settings")
        self.setModal(True)
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            QDialog {
                background: #2a2a2a;
                border: 2px solid #000000;
                border-radius: 8px;
            }
            QLabel {
                color: #eaeaea;
                font-size: 11px;
            }
            QLabel#section_title {
                color: #C8A2C8;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Title
        title = QLabel("Sample Chop Settings")
        title.setObjectName("section_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── Silence Threshold ──────────────────────────────────────────────
        sil_row = QHBoxLayout()
        sil_label = QLabel("Silence Threshold:")
        sil_label.setToolTip(
            "RMS amplitude below which audio is treated as silence.\n"
            "Lower = more sensitive (catches quieter gaps).\n"
            "Range: 0.00 – 1.00   Default: 0.01"
        )
        self.silence_spin = QDoubleSpinBox()
        self.silence_spin.setRange(0.0, 1.0)
        self.silence_spin.setSingleStep(0.01)
        self.silence_spin.setDecimals(3)
        self.silence_spin.setValue(0.01)
        self.silence_spin.setMinimumWidth(110)
        sil_row.addWidget(sil_label, 1)
        sil_row.addWidget(self.silence_spin)
        layout.addLayout(sil_row)

        # ── Transient Sensitivity ──────────────────────────────────────────
        trans_row = QHBoxLayout()
        trans_label = QLabel("Transient Sensitivity:")
        trans_label.setToolTip(
            "Multiplier for transient peak detection.\n"
            "Higher = snaps to transients more aggressively.\n"
            "Range: 0.1 – 10.0   Default: 1.5"
        )
        self.transient_spin = QDoubleSpinBox()
        self.transient_spin.setRange(0.1, 10.0)
        self.transient_spin.setSingleStep(0.1)
        self.transient_spin.setDecimals(1)
        self.transient_spin.setValue(1.5)
        self.transient_spin.setMinimumWidth(110)
        trans_row.addWidget(trans_label, 1)
        trans_row.addWidget(self.transient_spin)
        layout.addLayout(trans_row)

        # ── Pre-pad (ms) ───────────────────────────────────────────────────
        pre_row = QHBoxLayout()
        pre_label = QLabel("Pre-pad (ms):")
        pre_label.setToolTip(
            "Milliseconds of audio to keep before a detected onset.\n"
            "Increase if slice attacks are getting clipped.\n"
            "Default: 20 ms"
        )
        self.pre_spin = QSpinBox()
        self.pre_spin.setRange(0, 500)
        self.pre_spin.setSingleStep(5)
        self.pre_spin.setValue(20)
        self.pre_spin.setSuffix(" ms")
        self.pre_spin.setMinimumWidth(110)
        pre_row.addWidget(pre_label, 1)
        pre_row.addWidget(self.pre_spin)
        layout.addLayout(pre_row)

        # ── Post-pad (ms) ──────────────────────────────────────────────────
        post_row = QHBoxLayout()
        post_label = QLabel("Post-pad (ms):")
        post_label.setToolTip(
            "Milliseconds of audio to keep after a detected onset.\n"
            "Increase if tails / reverb are getting cut off.\n"
            "Default: 80 ms"
        )
        self.post_spin = QSpinBox()
        self.post_spin.setRange(0, 2000)
        self.post_spin.setSingleStep(10)
        self.post_spin.setValue(80)
        self.post_spin.setSuffix(" ms")
        self.post_spin.setMinimumWidth(110)
        post_row.addWidget(post_label, 1)
        post_row.addWidget(self.post_spin)
        layout.addLayout(post_row)

        # ── Min Slice (ms) ─────────────────────────────────────────────────
        min_row = QHBoxLayout()
        min_label = QLabel("Min Slice (ms):")
        min_label.setToolTip(
            "Shortest allowed slice. Slices shorter than this are discarded.\n"
            "Raise to filter out clicks and ultra-short noise hits.\n"
            "Default: 50 ms"
        )
        self.min_spin = QSpinBox()
        self.min_spin.setRange(10, 5000)
        self.min_spin.setSingleStep(10)
        self.min_spin.setValue(50)
        self.min_spin.setSuffix(" ms")
        self.min_spin.setMinimumWidth(110)
        min_row.addWidget(min_label, 1)
        min_row.addWidget(self.min_spin)
        layout.addLayout(min_row)

        # ── Max Slice (ms) ─────────────────────────────────────────────────
        max_row = QHBoxLayout()
        max_label = QLabel("Max Slice (ms):")
        max_label.setToolTip(
            "Longest allowed slice. Slices longer than this are split.\n"
            "Lower to break up sustained notes or long ambiences.\n"
            "Default: 10000 ms (10 s)"
        )
        self.max_spin = QSpinBox()
        self.max_spin.setRange(100, 60000)
        self.max_spin.setSingleStep(500)
        self.max_spin.setValue(10000)
        self.max_spin.setSuffix(" ms")
        self.max_spin.setMinimumWidth(110)
        max_row.addWidget(max_label, 1)
        max_row.addWidget(self.max_spin)
        layout.addLayout(max_row)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("apply_btn")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setStyleSheet("background: #555; color: #eaeaea;")
        btn_row.addStretch()
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.apply_btn)
        layout.addLayout(btn_row)

        # Wire buttons
        self.apply_btn.clicked.connect(self._on_apply)
        self.cancel_btn.clicked.connect(self.reject)

        # Load current values from config
        self._load_from_config()

    def _load_from_config(self):
        """Populate spinboxes from AppConfig.chop if available."""
        if self.app_config is None:
            return
        chop = getattr(self.app_config, 'chop', None)
        if chop is None:
            return
        self.silence_spin.setValue(float(getattr(chop, 'silence_threshold', 0.01)))
        self.transient_spin.setValue(float(getattr(chop, 'transient_sensitivity', 1.5)))
        self.pre_spin.setValue(int(getattr(chop, 'pre_ms', 20)))
        self.post_spin.setValue(int(getattr(chop, 'post_ms', 80)))
        self.min_spin.setValue(int(getattr(chop, 'min_slice_ms', 50)))
        self.max_spin.setValue(int(getattr(chop, 'max_slice_ms', 10000)))

    def _on_apply(self):
        """Save spinbox values to AppConfig.chop and close."""
        if self.app_config is not None:
            chop = getattr(self.app_config, 'chop', None)
            if chop is not None:
                chop.silence_threshold    = self.silence_spin.value()
                chop.transient_sensitivity = self.transient_spin.value()
                chop.pre_ms               = self.pre_spin.value()
                chop.post_ms              = self.post_spin.value()
                chop.min_slice_ms         = self.min_spin.value()
                chop.max_slice_ms         = self.max_spin.value()
        self.accept()

