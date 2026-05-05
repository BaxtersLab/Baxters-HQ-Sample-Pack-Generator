 # --- Ensure bspg and hqspg packages are importable regardless of launch directory ---
import sys, os
ROOT = os.path.dirname(os.path.abspath(__file__))
BSPG_PATH = os.path.join(ROOT, "bspg")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)          # makes `hqspg` importable
if BSPG_PATH not in sys.path:
    sys.path.insert(0, BSPG_PATH)     # makes `bspg` importable

from PySide6.QtWidgets import QApplication
import atexit
import time

try:
    from appdirs import user_data_dir
except Exception:
    user_data_dir = None


def get_lock_file_path() -> str:
    app_name = 'HQSPG'
    app_author = 'BaxtersHQ'
    if user_data_dir is not None:
        base_dir = user_data_dir(app_name, app_author)
    else:
        base_dir = os.path.join(os.path.expanduser('~'), '.hqspg')
    try:
        os.makedirs(base_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(base_dir, 'hqspg_instance.lock')


LOCKFILE = get_lock_file_path()


def acquire_lock():
    """
    Acquire a single-instance lock.
    On Windows: uses a named kernel mutex (guaranteed OS-level, survives crashes cleanly).
    On other platforms: uses an exclusive file lock via fcntl.
    Returns a handle on success, None if another instance is already running.
    """
    if sys.platform == 'win32':
        import ctypes
        import ctypes.wintypes
        _MUTEX_NAME = 'Global\\BaxtersHQSPG_SingleInstance_v1'
        ERROR_ALREADY_EXISTS = 183
        handle = ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
        if handle == 0:
            return None  # CreateMutex failed entirely
        if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            ctypes.windll.kernel32.CloseHandle(handle)
            return None  # another instance owns the mutex
        return handle  # we own it; keep alive until process exits
    else:
        try:
            import fcntl
            f = open(LOCKFILE, 'w')
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                f.write(str(os.getpid()))
                f.flush()
                return f
            except (IOError, OSError):
                try:
                    f.close()
                except Exception:
                    pass
                return None
        except Exception:
            return None


def release_lock(fobj):
    """Release the lock handle acquired by acquire_lock."""
    if fobj is None:
        return
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.kernel32.ReleaseMutex(fobj)
            ctypes.windll.kernel32.CloseHandle(fobj)
        except Exception:
            pass
    else:
        try:
            import fcntl
            fcntl.flock(fobj.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            fobj.close()
        except Exception:
            pass
        try:
            if os.path.exists(LOCKFILE):
                os.remove(LOCKFILE)
        except Exception:
            pass


def main():
    # Single-instance enforcement
    lock = acquire_lock()
    if lock is None:
        # Show a visible dialog before exiting so the user knows why nothing opened
        _app = QApplication.instance() or QApplication(sys.argv)
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Already Running")
        msg.setText("Baxter's HQ Sample Pack Generator is already open.\n\nCheck your taskbar.")
        msg.setIcon(QMessageBox.Warning)
        msg.exec()
        sys.exit(0)
    
    # Register cleanup on exit
    atexit.register(lambda: release_lock(lock))

    try:
        print('DEBUG: importing MainWindow...', flush=True)
        from bspg.gui.main_window import MainWindow
        print('DEBUG: imported MainWindow successfully', flush=True)
    except Exception as e:
        print('Failed to import MainWindow:', e)
        release_lock(lock)
        raise

    print('DEBUG: creating QApplication', flush=True)
    app = QApplication(sys.argv)

    # --- App identity: name + icon so Task Manager shows BaxtersHQSPG, not python ---
    app.setApplicationName('BaxtersHQSPG')
    app.setApplicationDisplayName("Baxter's HQ Sample Pack Generator")
    app.setOrganizationName('BaxtersHQ')

    _ICON_PATH = os.path.join(ROOT, 'hqspg', 'assets', 'hqspg_icon.ico')
    if os.path.isfile(_ICON_PATH):
        from PySide6.QtGui import QIcon
        _app_icon = QIcon(_ICON_PATH)
        app.setWindowIcon(_app_icon)
    else:
        _app_icon = None

    # Windows: set AppUserModelID so the taskbar groups by app name, not python.exe
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('BaxtersHQ.HQSPG.1')
        except Exception:
            pass
    # -----------------------------------------------------------------------

    # Load AppConfig once at startup and pass the instance into the MainWindow
    try:
        from bspg.core.config import AppConfig
        app_conf = AppConfig()
        try:
            app_conf.load()
        except Exception:
            pass
    except Exception:
        app_conf = None

    print('DEBUG: instantiating MainWindow', flush=True)
    win = MainWindow(app_config=app_conf)
    print('DEBUG: MainWindow instantiated', flush=True)

    # Apply icon to the main window as well
    if _app_icon is not None:
        win.setWindowIcon(_app_icon)
    win.setWindowTitle("Baxter's HQ Sample Pack Generator")

    win.show()
    print('DEBUG: window show() called', flush=True)
    # --- FORCE WINDOW ON-SCREEN ---
    try:
        geom = win.frameGeometry()
        screen = app.primaryScreen().availableGeometry()
        if not screen.contains(geom.center()):
            print('FIX: Window was off-screen, moving to center', flush=True)
            win.move(screen.center() - geom.center())
    except Exception:
        pass
    # --- END FORCE WINDOW ON-SCREEN ---
    # --- DIAGNOSTIC BLOCK ---
    import traceback
    from PySide6.QtWidgets import QWidget

    try:
        cw = win.centralWidget()
        print('DIAG: centralWidget =', cw, flush=True)

        if cw is None:
            print('DIAG: centralWidget is None (fatal)', flush=True)
        else:
            print('DIAG: centralWidget type =', type(cw), flush=True)
            try:
                layout = cw.layout()
                print('DIAG: centralWidget layout =', layout, flush=True)
                if layout is not None:
                    try:
                        print('DIAG: centralWidget layout count =', layout.count(), flush=True)
                    except Exception as e:
                        print('DIAG: layout.count() error:', e, flush=True)
            except Exception as e:
                print('DIAG: centralWidget layout error:', e, flush=True)
            try:
                children = cw.findChildren(QWidget)
                print('DIAG: centralWidget QWidget children count =', len(children), flush=True)
            except Exception as e:
                print('DIAG: findChildren error:', e, flush=True)

        try:
            print('DIAG: hasattr _terms_overlay:', hasattr(win, '_terms_overlay'), flush=True)
            if hasattr(win, '_terms_overlay'):
                print('DIAG: _terms_overlay =', getattr(win, '_terms_overlay'), flush=True)
        except Exception as e:
            print('DIAG: _terms_overlay check error:', e, flush=True)

        try:
            print('DIAG: hasattr settings_panel:', hasattr(win, 'settings_panel'), flush=True)
            print('DIAG: MainWindow children count:', len(win.children()), flush=True)
        except Exception as e:
            print('DIAG: MainWindow children error:', e, flush=True)

    except Exception:
        print('DIAG: Exception during diagnostics:', flush=True)
        traceback.print_exc()
    # --- END DIAGNOSTIC BLOCK ---

    try:
        print('DEBUG: entering event loop', flush=True)
        # --- GEOMETRY DIAGNOSTICS ---
        try:
            cw = win.centralWidget()
            print('GEOM: centralWidget =', cw, flush=True)
            if cw:
                try:
                    print('GEOM: cw.size =', cw.size(), flush=True)
                    print('GEOM: cw.geometry =', cw.geometry(), flush=True)
                    print('GEOM: cw.rect =', cw.rect(), flush=True)
                    print('GEOM: cw.isVisible =', cw.isVisible(), flush=True)
                except Exception as e:
                    print('GEOM: error querying cw geometry:', e, flush=True)

                layout = cw.layout()
                print('GEOM: layout =', layout, flush=True)
                if layout:
                    try:
                        print('GEOM: layout.count =', layout.count(), flush=True)
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            w = item.widget()
                            print(f'GEOM: item {i} widget =', w, flush=True)
                            if w:
                                try:
                                    print(f'GEOM: item {i} size =', w.size(), flush=True)
                                    print(f'GEOM: item {i} geometry =', w.geometry(), flush=True)
                                    print(f'GEOM: item {i} rect =', w.rect(), flush=True)
                                    print(f'GEOM: item {i} visible =', w.isVisible(), flush=True)
                                except Exception as e:
                                    print(f'GEOM: item {i} geometry error:', e, flush=True)
                    except Exception as e:
                        print('GEOM: error iterating layout items:', e, flush=True)
        except Exception as e:
            import traceback
            print('GEOM: Exception during geometry dump:', flush=True)
            traceback.print_exc()
        # --- END GEOMETRY DIAGNOSTICS ---
        # --- STYLE / TOP-LEVEL WIDGETS DIAGNOSTICS ---
        try:
            from PySide6.QtGui import QPalette
            from PySide6.QtCore import Qt
            try:
                print('STYLE: app.styleSheet =', app.styleSheet(), flush=True)
            except Exception:
                print('STYLE: app.styleSheet error', flush=True)
            try:
                print('STYLE: win.styleSheet =', win.styleSheet(), flush=True)
            except Exception:
                print('STYLE: win.styleSheet error', flush=True)
            try:
                cw = win.centralWidget()
                print('STYLE: cw.styleSheet =', cw.styleSheet() if cw is not None else None, flush=True)
            except Exception:
                print('STYLE: cw.styleSheet error', flush=True)

            try:
                pal = app.palette()
                def col(role):
                    try:
                        return pal.color(role).name()
                    except Exception:
                        return '<err>'
                from PySide6.QtGui import QPalette as _QP
                print('STYLE: palette Window=', col(_QP.Window), ' Base=', col(_QP.Base), ' WindowText=', col(_QP.WindowText), ' Text=', col(_QP.Text), flush=True)
            except Exception:
                print('STYLE: palette error', flush=True)

            try:
                # List top-level widgets to find any unexpected overlays
                from PySide6.QtWidgets import QApplication as _QApp
                tops = _QApp.topLevelWidgets()
                print('STYLE: topLevelWidgets count =', len(tops), flush=True)
                for i, tw in enumerate(tops):
                    try:
                        print(f'STYLE: top {i} =', tw, 'geom=', tw.geometry(), 'visible=', tw.isVisible(), 'flags=', int(tw.windowFlags()), flush=True)
                        ss = tw.styleSheet()
                        print(f'STYLE: top {i} styleSheet =', ss if ss else '<empty>', flush=True)
                    except Exception:
                        print(f'STYLE: top {i} info error', flush=True)
            except Exception:
                print('STYLE: topLevelWidgets error', flush=True)
        except Exception:
            import traceback
            print('STYLE: Exception during style diagnostics', flush=True)
            traceback.print_exc()

        # Schedule a brief screenshot grab of the main window and central widget for visual inspection
        try:
            from PySide6.QtCore import QTimer
            from PySide6.QtGui import QPixmap
            def _save_screenshot():
                try:
                    path = os.path.join(ROOT, 'diag_window.png')
                    try:
                        pm = win.grab()
                    except Exception:
                        pm = None
                    if pm is not None:
                        pm.save(path)
                        print('STYLE: saved window screenshot to', path, flush=True)
                    else:
                        print('STYLE: grab failed', flush=True)
                except Exception as e:
                    print('STYLE: screenshot error', e, flush=True)
            QTimer.singleShot(500, _save_screenshot)
        except Exception:
            print('STYLE: scheduling screenshot failed', flush=True)

            # --- PAINT WRAPPER FOR FLOWCHART ---
            try:
                import types, traceback
                fc = win.findChild(QWidget, 'flowchart_container')
                if fc is None:
                    print('PAINT: flowchart_container not found', flush=True)
                else:
                    try:
                        orig = fc.paintEvent
                    except Exception:
                        orig = None
                    if orig is None:
                        print('PAINT: no original paintEvent found on flowchart_container', flush=True)
                    else:
                        def safe_paint(self, ev):
                            try:
                                return orig(ev)
                            except Exception:
                                print('PAINT: Exception in flowchart_container.paintEvent', flush=True)
                                traceback.print_exc()
                                raise
                        try:
                            fc.paintEvent = types.MethodType(safe_paint, fc)
                            print('PAINT: wrapped flowchart_container.paintEvent', flush=True)
                        except Exception as e:
                            print('PAINT: error binding paintEvent:', e, flush=True)
            except Exception as e:
                print('PAINT: setup error:', e, flush=True)
            # --- END PAINT WRAPPER ---

        sys.exit(app.exec())
    finally:
        release_lock(lock)


if __name__ == '__main__':
    main()
