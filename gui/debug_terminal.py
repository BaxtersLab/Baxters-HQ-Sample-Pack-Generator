from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt


class DebugTerminal(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName('DebugTerminal')
        self.setStyleSheet('''
            #DebugTerminal {
                background: transparent;
                color: #007BFF;
                border: none;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
            }
        ''')

    def append_log(self, message: str):
        # Ensure thread-safe append
        try:
            self.append(message)
            # keep caret at bottom
            self.moveCursor(self.textCursor().End)
        except Exception:
            pass
