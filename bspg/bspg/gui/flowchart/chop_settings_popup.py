from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QPushButton, QWidget
)
from PySide6.QtCore import Qt


class ChopSettingsPopup(QDialog):
    """
    Lavender gear-button popup for Sample Chop adjustments.

    Controls:
        silence_threshold    — RMS level below which audio is treated as silence
                               range 0.00 – 1.00, step 0.01, default 0.01
        transient_sensitivity — multiplier for transient detection peaks
                               range 0.1 – 10.0, step 0.1, default 1.5
    """

    def __init__(self, app_config=None, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self.setWindowTitle("Sample Chop Settings")
        self.setModal(True)
        self.setMinimumWidth(300)
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
        layout.setSpacing(12)

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
        self.silence_spin.setSuffix("  silence")
        self.silence_spin.setMinimumWidth(120)
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
        self.transient_spin.setSuffix("  transient")
        self.transient_spin.setMinimumWidth(120)
        trans_row.addWidget(trans_label, 1)
        trans_row.addWidget(self.transient_spin)
        layout.addLayout(trans_row)

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

    def _on_apply(self):
        """Save spinbox values to AppConfig.chop and close."""
        if self.app_config is not None:
            chop = getattr(self.app_config, 'chop', None)
            if chop is not None:
                chop.silence_threshold = self.silence_spin.value()
                chop.transient_sensitivity = self.transient_spin.value()
        self.accept()
