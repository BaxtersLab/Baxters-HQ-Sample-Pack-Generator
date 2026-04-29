# import-only check for resources and GUI components
import sys
import os

# ensure project root is on sys.path
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

try:
    import gui.resources_rc as resources_rc
except Exception:
    try:
        from gui import resources_rc
    except Exception:
        pass

from gui.main_window import MainWindow
from gui.advanced_panel import AdvancedPanel
from gui.hrt_status_widget import HRTStatusWidget

print("IMPORT_OK")
