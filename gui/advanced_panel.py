from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from .hrt_status_widget import HRTStatusWidget
from hqspg.integration.hotrod_connector import HotRodConnector

class AdvancedPanel(QWidget):
    def __init__(self, debug_terminal=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")

        layout = QVBoxLayout(self)

        self.hrt_status = HRTStatusWidget()
        self.link_button = QPushButton("Link to Hot Rod Tuner")
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)

        layout.addWidget(self.hrt_status)
        layout.addWidget(self.link_button)
        layout.addWidget(self.disconnect_button)

        self._connector = HotRodConnector()
        self._debug_terminal = debug_terminal

        # Callbacks
        self._connector.set_callback("on_log", self._on_log)
        self._connector.set_callback("on_connect", self._on_connect)
        self._connector.set_callback("on_disconnect", self._on_disconnect)
        self._connector.set_callback("on_linked", self._on_linked)
        self._connector.set_callback("on_unlinked", self._on_unlinked)

        self.link_button.clicked.connect(self._on_link_clicked)
        self.disconnect_button.clicked.connect(self._on_disconnect_clicked)

        self.hrt_status.set_disconnected()

    def _on_log(self, msg: str):
        if self._debug_terminal:
            self._debug_terminal.append_log(msg)

    def _on_link_clicked(self):
        self.hrt_status.set_connecting()
        self.link_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self._connector.connect()

    def _on_disconnect_clicked(self):
        self._connector.disconnect()
        self.hrt_status.set_disconnected()
        self.link_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)

    def _on_connect(self):
        self._on_log("HRT TCP connected; awaiting handshake_ok...")

    def _on_disconnect(self):
        self._on_log("HRT TCP disconnected.")
        self.hrt_status.set_disconnected()
        self.link_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)

    def _on_linked(self):
        self._on_log("HRT handshake_ok; link established.")
        self.hrt_status.set_linked()

    def _on_unlinked(self):
        self._on_log("HRT link lost or handshake error.")
        self.hrt_status.set_error()
