from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
from .advanced_panel import AdvancedPanel
from .debug_terminal import DebugTerminal
from hqspg._version import __product_name__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Use product name for window title
        try:
            self.setWindowTitle(__product_name__ + " Standalone")
        except Exception:
            self.setWindowTitle("Standalone")

        self._central = QWidget()
        self.setCentralWidget(self._central)

        self.layout = QVBoxLayout(self._central)

        self.run_button = QPushButton("Run Pipeline")
        self.advanced_button = QPushButton("Advanced Settings")
        self.debug_button = QPushButton("Debug Terminal")

        self.layout.addWidget(self.run_button)
        self.layout.addWidget(self.advanced_button)
        self.layout.addWidget(self.debug_button)

        self.debug_terminal = DebugTerminal()
        self.advanced_panel = AdvancedPanel(debug_terminal=self.debug_terminal)

        self.advanced_button.clicked.connect(self._open_advanced)
        self.debug_button.clicked.connect(self._open_debug)

    def _open_advanced(self):
        self.advanced_panel.show()

    def _open_debug(self):
        self.debug_terminal.show()
