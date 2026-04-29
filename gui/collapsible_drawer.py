from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Property, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPainter, QBrush, QColor
from .debug_terminal import DebugTerminal


class CollapsibleDrawer(QFrame):
    def __init__(self, parent=None, target_height=250):
        super().__init__(parent)
        self._target_height = target_height
        self._is_expanded = False
        self.setObjectName('CollapsibleDrawer')
        self.setMaximumHeight(0)
        self.setMinimumHeight(0)

        self.setStyleSheet("""
        #CollapsibleDrawer {
            background: #1a1a1a;
            border: 2px solid #000;
            border-radius: 18px;
        }
        """)

        self.anim = QPropertyAnimation(self, b"maximumHeight")
        self.anim.setDuration(240)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

        # Debug terminal widget
        self.terminal = DebugTerminal(self)
        self.layout.addWidget(self.terminal)

    @property
    def is_expanded(self):
        return self._is_expanded

    def expand(self):
        if self._is_expanded:
            return
        self.anim.stop()
        self.anim.setStartValue(0)
        self.anim.setEndValue(self._target_height)
        self.anim.start()
        self._is_expanded = True

    def collapse(self):
        if not self._is_expanded:
            return
        self.anim.stop()
        self.anim.setStartValue(self.maximumHeight())
        self.anim.setEndValue(0)
        self.anim.start()
        self._is_expanded = False

    # optional setter to adjust target
    def set_target_height(self, h: int):
        self._target_height = h
