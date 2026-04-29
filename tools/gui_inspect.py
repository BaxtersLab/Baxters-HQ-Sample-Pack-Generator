import sys
import os
from PySide6.QtWidgets import QApplication

proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from gui.main import MainWindow
from PySide6.QtGui import QImage

app = QApplication([])
win = MainWindow()
# don't show, just inspect
print('TITLE:', win.windowTitle())
central = win.centralWidget()
if central is not None:
    print('CENTRAL_OBJNAME:', central.objectName())
    # show the first 200 chars of stylesheet for inspection
    style = central.styleSheet()
    print('CENTRAL_STYLE_SNIPPET:', style[:200].replace('\n','\\n'))
else:
    print('NO_CENTRAL')

# check resource load directly
q = QImage(':/assets/background.png')
print('RESOURCE_QIMAGE_isNull:', q.isNull())
print('RESOURCE_QIMAGE_size:', q.width(), q.height())

# clean exit
app.quit()
