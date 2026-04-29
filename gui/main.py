import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QIcon, QPainterPath, QRegion
from .widgets import TopBar, BottomBar, CustomTitleBar
from .controller import Controller
from .log import setup_gui_logger
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Slot
from .collapsible_drawer import CollapsibleDrawer
from hqspg._version import __version__, __app_name__, __product_name__
import socket

logger = setup_gui_logger()

HERE = os.path.dirname(__file__)
ASSETS = os.path.normpath(os.path.join(HERE, '..', 'assets'))


def load_stylesheet(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName('MainWindow')
        # create a frameless, translucent window so corners can be rounded
        try:
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            # remove OS drop shadow to avoid visual artifacts around rounded corners
            try:
                self.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            except Exception:
                pass
        except Exception:
            pass
        # Use product name constant for visible UI title
        try:
            self.setWindowTitle(f'{__product_name__}')
        except Exception:
            self.setWindowTitle('')
        self.resize(1100, 700)
        self._setup_ui()
        # apply styles (this imports compiled resources so :/ paths resolve)
        self._apply_styles()
        # update backdrop after styles/resources are available
        self._update_backdrop()

    def _setup_ui(self):
        central = QWidget(self)
        central.setObjectName('CentralWidget')
        self.setCentralWidget(central)

        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # custom titlebar: create as a child (not in the layout) and reserve
        # the top layout margin so the central content is pushed below it.
        # move the bar up slightly so it hides corner artifacts without
        # increasing its visual height.
        self.title_bar = CustomTitleBar(self)
        try:
            extra_move = 8
            tb_h = max(self.title_bar.height(), 36)
            new_h = tb_h + extra_move
            # make titlebar slightly taller so its rounded corners fully show
            self.title_bar.setFixedHeight(new_h)
            v.setContentsMargins(0, new_h, 0, 0)
            # ensure titlebar initially spans the full width and sits at the top
            self.title_bar.setFixedWidth(self.width())
            self.title_bar.move(0, 0)
            self._titlebar_overlap = 0
        except Exception:
            # fallback: reserve original height and position at top
            v.setContentsMargins(0, self.title_bar.height(), 0, 0)

        # top 30, middle 35, bottom 35 via stretch factors
        self.top_band = QWidget()
        self.top_band.setObjectName('TopBand')
        self.top_layout = QVBoxLayout(self.top_band)
        self.top_layout.setContentsMargins(12, 12, 12, 12)
        self.top_bar = TopBar(self)
        self.top_layout.addWidget(self.top_bar)

        self.logo_band = QWidget()
        self.logo_band.setObjectName('LogoBand')
        # intentionally empty

        self.bottom_band = QWidget()
        self.bottom_band.setObjectName('BottomBand')
        self.bottom_layout = QVBoxLayout(self.bottom_band)
        self.bottom_layout.setContentsMargins(12, 12, 12, 12)
        self.bottom_bar = BottomBar(self)
        self.bottom_layout.addWidget(self.bottom_bar)

        # favor the central/logo band so the backdrop image fills most of the window
        v.addWidget(self.top_band, 10)
        v.addWidget(self.logo_band, 80)
        v.addWidget(self.bottom_band, 10)

        # debug drawer sits below bottom band
        self.debug_drawer = CollapsibleDrawer(self, target_height=250)
        # start collapsed
        self.debug_drawer.collapse()
        # integrate bspg logger with existing debug terminal if adapter available
        try:
            from bspg.gui.debug_terminal.debug_terminal_widget import integrate_with_existing

            try:
                integrate_with_existing(self.debug_drawer.terminal)
            except Exception:
                pass
        except Exception:
            # bspg package or integration helper not present; skip
            pass
        v.addWidget(self.debug_drawer, 0)

        # controller
        self.controller = Controller()
        # connect controller signals
        self.controller.progress.connect(self.bottom_bar.progress.setValue)
        self.controller.finished.connect(self._on_pipeline_finished)
        self.controller.error.connect(self._on_pipeline_error)
        self.controller.status.connect(lambda s: logger.info('Status: %s', s))

        # connect signals from widgets to controller actions
        # Backdrop/backsplash toggle moved into SettingsPanel
        self.top_bar.debug_toggled.connect(self.toggle_debug_drawer)

        # bottom bar Settings button will open a settings panel containing actions
        from .settings_panel import SettingsPanel
        self.settings_panel = SettingsPanel(self)
        # connect minimal settings panel actions
        self.settings_panel.backsplash_toggled.connect(self.on_toggle_backdrop)
        self.settings_panel.hover_toggled.connect(self._on_hover_toggled)
        self.settings_panel.hotrod_link_clicked.connect(self._on_hotrod_link_clicked)

        self.bottom_bar.generate.connect(self._on_generate_clicked)
        # randomize action removed — not used in this app
        self.bottom_bar.export.connect(self._on_export_clicked)
        self.bottom_bar.settings_btn.clicked.connect(self._open_settings)

        # (backsplash toggle already connected above)

        # Buttons list used to enable/disable during pipeline; include bottom-bar action buttons
        self._buttons = [self.bottom_bar.generate_btn, self.bottom_bar.export_btn]

        # default backdrop
        self.backdrop_on = True

        # attempt to size the window to the backdrop image for tighter fit
        try:
            qimg = QImage(':/assets/background.png')
            if not qimg.isNull():
                # add small chrome for bars
                target_w = qimg.width() + 40
                target_h = qimg.height() + 140
                # only resize if smaller than current default
                self.resize(min(target_w, self.width()), min(target_h, self.height()))
        except Exception:
            pass

        # apply user-requested global scale reduction: width -20%, height -15%
        try:
            new_w = int(self.width() * 0.80)
            new_h = int(self.height() * 0.85)
            self.resize(new_w, new_h)
        except Exception:
            pass
        # additional reduction requested by user: scale down by 8%
        try:
            new_w = int(self.width() * 0.92)
            new_h = int(self.height() * 0.92)
            self.resize(new_w, new_h)
        except Exception:
            pass

        # further user-requested reduction: scale down by an additional 10%
        try:
            new_w = int(self.width() * 0.90)
            new_h = int(self.height() * 0.90)
            self.resize(new_w, new_h)
        except Exception:
            pass

        # connect controller logs to debug terminal
        self.controller.log.connect(lambda m: self.debug_drawer.terminal.append_log(m))
        # respond to status changes to disable/enable UI
        self.controller.status.connect(self._on_status_changed)
        # status/footer: hide status bar (dev version info removed)
        try:
            if self.statusBar():
                self.statusBar().hide()
        except Exception:
            pass

    def toggle_debug_drawer(self):
        if self.debug_drawer.is_expanded:
            self.debug_drawer.collapse()
        else:
            self.debug_drawer.expand()

    def _open_settings(self):
        # show settings as a non-modal window positioned near bottom-right
        logger.info('Settings button pressed; opening settings panel')
        sp = self.settings_panel
        sp.resize(320, 320)
        # position at right side of bottom band using global coordinates and
        # ensure the panel is shown above the main window as a tool window
        try:
            sp.setWindowFlag(Qt.Tool, True)
            bottom_right = self.mapToGlobal(self.rect().bottomRight())
            sp.move(bottom_right.x() - sp.width() - 16, bottom_right.y() - sp.height() - 56)
            sp.show()
            sp.raise_()
            sp.activateWindow()
        except Exception:
            # best-effort fallback
            pass

    def _on_hover_toggled(self, enabled: bool):
        logger.info('Hover Logic toggled: %s', enabled)
        try:
            self.hover_logic_enabled = bool(enabled)
        except Exception:
            pass

    def _on_hotrod_link_clicked(self):
        # Open the AdvancedPanel which contains the Hot Rod connector UI
        try:
            from .advanced_panel import AdvancedPanel
            ap = AdvancedPanel(debug_terminal=self.debug_drawer.terminal)
            ap.setWindowFlag(Qt.Tool, True)
            # position near settings button
            pos = self.mapToGlobal(self.rect().bottomRight())
            ap.resize(360, 240)
            ap.move(pos.x() - ap.width() - 16, pos.y() - ap.height() - 56)
            ap.show()
            ap.raise_()
            ap.activateWindow()
        except Exception:
            logger.exception('Failed to open AdvancedPanel for Hot Rod link')
            sp.show()

    def _apply_styles(self):
        # ensure compiled Qt resources are imported so :/ paths resolve
        try:
            from . import resources_rc  # generated by pyrcc6
        except Exception:
            pass
        qss = load_stylesheet(os.path.join(os.path.dirname(__file__), 'styles.qss'))
        if qss:
            # if the Qt resource isn't actually registered (pyrcc6 not run),
            # replace the resource URL in the QSS with a filesystem fallback so
            # styles render without missing-resource warnings.
            try:
                probe = QImage(':/assets/background.png')
                resource_ok = not probe.isNull()
            except Exception:
                resource_ok = False

            if not resource_ok:
                fs_img = os.path.join(ASSETS, 'BHQSPGBackdrop.png')
                qss = qss.replace(':/assets/background.png', fs_img.replace('\\', '/'))

            self.setStyleSheet(qss)

    def on_toggle_backdrop(self, off: bool):
        self.backdrop_on = not bool(off)
        self._update_backdrop()

    @Slot()
    def _on_load_clicked(self):
        # choose file or folder
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.ExistingFile)
        path, _ = fd.getOpenFileName(self, 'Select audio file')
        if path:
            logger.info('Selected input: %s', path)
            files = self.controller.load_input(path)
            if files:
                # prefer first returned file
                self.current_input = files[0]
                logger.info('Controller resolved input: %s', self.current_input)
            else:
                self.current_input = path

    @Slot()
    def _on_save_clicked(self):
        path = QFileDialog.getExistingDirectory(self, 'Select output directory')
        if path:
            self.current_output = path
            logger.info('Selected output: %s', path)
            self.controller.save_output(path)

    @Slot()
    def _on_generate_clicked(self):
        # disable buttons
        for b in self._buttons:
            b.setEnabled(False)
        self.bottom_bar.progress.setValue(0)
        input_path = getattr(self, 'current_input', None)
        if not input_path:
            QMessageBox.warning(self, 'No input', 'Please choose an input file first')
            for b in self._buttons:
                b.setEnabled(True)
            return
        # collect extractor params from UI and run full pipeline
        extractor_cfg = {
            'silence_threshold': float(self.top_bar.silence_spin.value()),
            'transient_sensitivity': float(self.top_bar.transient_spin.value())
        }
        cfg = {'extractor': extractor_cfg}
        logger.info('Starting full pipeline for %s with cfg=%s', input_path, cfg)
        self.controller.run_full_pipeline(input_path, config=cfg, output_base=getattr(self, 'current_output', None))

    @Slot()
    def _on_export_clicked(self):
        dest = QFileDialog.getExistingDirectory(self, 'Select export directory')
        if dest:
            src = getattr(self, 'current_output', None)
            if not src:
                QMessageBox.warning(self, 'No output', 'Please set an output directory first via Save')
                return
            logger.info('Export directory chosen: %s', dest)
            self.controller.export_output(src, dest)

    def _on_status_changed(self, status_msg: str):
        # disable UI during any starting/working status
        if isinstance(status_msg, str) and ('Starting' in status_msg):
            for b in self._buttons:
                b.setEnabled(False)
        elif status_msg in ('Finished', 'Error'):
            for b in self._buttons:
                b.setEnabled(True)

    @Slot(object)
    def _on_pipeline_finished(self, result):
        logger.info('Pipeline finished: %s', result)
        self.bottom_bar.progress.setValue(100)
        for b in self._buttons:
            b.setEnabled(True)
        QMessageBox.information(self, 'Done', 'Pipeline completed')

    @Slot(str)
    def _on_pipeline_error(self, err):
        logger.error('Pipeline error: %s', err)
        # flash progress red via stylesheet
        self.bottom_bar.progress.setStyleSheet('QProgressBar { background: #ffdddd; }')
        for b in self._buttons:
            b.setEnabled(True)
        QMessageBox.critical(self, 'Error', f'Pipeline error:\n{err}')

    def _update_backdrop(self):
        central = self.centralWidget()
        if self.backdrop_on:
            # prefer Qt resource-backed image
            try:
                qimg = QImage(':/assets/background.png')
            except Exception:
                qimg = QImage()
            if not qimg.isNull():
                # compute image brightness and pick a contrasting background
                try:
                    w, h = qimg.width(), qimg.height()
                    sx = max(1, w // 10)
                    sy = max(1, h // 10)
                    total = 0.0
                    count = 0
                    for x in range(0, w, sx):
                        for y in range(0, h, sy):
                            c = qimg.pixelColor(x, y)
                            lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
                            total += lum
                            count += 1
                    mean_lum = total / max(1, count)
                except Exception:
                    mean_lum = 255

                # if the image is dark, use a light backdrop for contrast
                if mean_lum < 64:
                    bg = '#ffffff'
                else:
                    bg = 'transparent'

                central.setStyleSheet(f"QWidget#CentralWidget {{background-image: url(':/assets/background.png'); background-position: center; background-repeat: no-repeat; background-color: {bg};}}")
            else:
                # fallback to existing filesystem image path if resource not present
                img = os.path.join(ASSETS, 'BHQSPGBackdrop.png')
                if os.path.isfile(img):
                    central.setStyleSheet(f"QWidget#CentralWidget {{background-image: url('{img}'); background-position: center; background-repeat: no-repeat; background-color: transparent;}}")
                else:
                    central.setStyleSheet("QWidget#CentralWidget {background-color: #111;}")
        else:
            # when backdrop_off, fallback to a darker background
            central.setStyleSheet("QWidget#CentralWidget {background-color: #1a1a1a; color: #007BFF;}")

    def _apply_round_mask(self, radius: int = 18):
        try:
            rect = self.rect()
            path = QPainterPath()
            path.addRoundedRect(rect, radius, radius)
            region = QRegion(path.toFillPolygon().toPolygon())
            self.setMask(region)
        except Exception:
            try:
                self.clearMask()
            except Exception:
                pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self._apply_round_mask()
        except Exception:
            pass
        try:
            if hasattr(self, 'title_bar') and self.title_bar:
                self.title_bar.setFixedWidth(self.width())
                self.title_bar.move(0, 0)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        try:
            self._apply_round_mask()
        except Exception:
            pass
        try:
            if hasattr(self, 'title_bar') and self.title_bar:
                self.title_bar.setFixedWidth(self.width())
                self.title_bar.move(0, 0)
        except Exception:
            pass


def main():
    app = QApplication(sys.argv)
    # Intentionally do not set an application icon here so the titlebar
    # does not show an extra icon next to the window title during development.
    # For frozen builds use the packager (PyInstaller `--icon`) to embed an
    # executable icon instead of setting it at runtime.

    # single-instance guard: create a TCP loopback bind on a fixed port.
    # This is reliable cross-platform and avoids QLocalServer quirks.
    LOCK_PORT = 51837
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # try to request exclusive bind on Windows; fall back safely elsewhere
        try:
            if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                # ensure we don't allow another process to re-bind the same address
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        except Exception:
            pass
        s.bind(('127.0.0.1', LOCK_PORT))
        s.listen(1)
        # keep reference on app to avoid GC and keep the socket open
        app._single_lock_socket = s
    except Exception:
        try:
            print(f'{__product_name__} is already running (port lock). Only one instance is allowed.', file=sys.stderr)
        except Exception:
            pass
        return 0
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
