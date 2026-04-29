from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
import sys
app = QApplication([])
q = QImage(':/assets/background.png')
print('isNull', q.isNull())
print('w,h', q.width(), q.height())
app.quit()
