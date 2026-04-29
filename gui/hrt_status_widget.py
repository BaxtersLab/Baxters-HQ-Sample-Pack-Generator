from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import QSize

class Beacon(QWidget):
    def __init__(self, color: QColor):
        super().__init__()
        self.color = color

    def sizeHint(self):
        return QSize(16, 16)

    def paintEvent(self, event):
        d = min(self.width(), self.height())
        r = d - 2
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(self.color)
        painter.setPen(self.color)
        painter.drawEllipse((self.width()-r)//2, (self.height()-r)//2, r, r)


class HRTStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.beacon = Beacon(QColor(128, 128, 128))
        self.label = QLabel("HRT: Disconnected")

        layout.addWidget(self.beacon)
        layout.addWidget(self.label)

    def _set(self, color: QColor, text: str):
        self.beacon.color = color
        self.label.setText(text)
        self.beacon.update()
        self.update()

    def set_disconnected(self):
        self._set(QColor(128, 128, 128), "HRT: Disconnected")

    def set_connecting(self):
        self._set(QColor(255, 165, 0), "HRT: Connecting...")

    def set_linked(self):
        self._set(QColor(0, 200, 0), "HRT: Linked")

    def set_error(self):
        self._set(QColor(200, 0, 0), "HRT: Error")
