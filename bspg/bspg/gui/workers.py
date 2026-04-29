from PySide6.QtCore import QObject, Signal
from typing import Any, Dict
from bspg.core.logging import bspg_logger


class BaseWorker(QObject):
    sig_progress = Signal(float)
    sig_log = Signal(str)
    sig_finished = Signal(dict)
    sig_error = Signal(str)

    def __init__(self, config: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self.logger = bspg_logger

    def run(self) -> Dict[str, Any]:
        """Run the work synchronously. Subclasses should implement actual logic.

        Return a result dict. This base implementation emits a log and returns
        a generic success result.
        """
        try:
            self.logger.info('worker', f'Starting {self.__class__.__name__}')
            self.sig_log.emit(f'Starting {self.__class__.__name__}')
        except Exception:
            pass
        result = {'status': 'ok', 'worker': self.__class__.__name__}
        try:
            self.sig_finished.emit(result)
        except Exception:
            pass
        return result


class DemucsWorker(BaseWorker):
    def run(self) -> Dict[str, Any]:
        try:
            self.logger.info('demucs', 'Running Demucs extraction (placeholder)')
            self.sig_log.emit('Demucs: placeholder extraction')
        except Exception:
            pass
        res = {'status': 'ok', 'stage': 'demucs'}
        try:
            self.sig_finished.emit(res)
        except Exception:
            pass
        return res


class RepairWorker(BaseWorker):
    def run(self) -> Dict[str, Any]:
        try:
            self.logger.info('repair', 'Running repair/generative (placeholder)')
            self.sig_log.emit('Repair: placeholder')
        except Exception:
            pass
        res = {'status': 'ok', 'stage': 'repair'}
        try:
            self.sig_finished.emit(res)
        except Exception:
            pass
        return res


class SlicerWorker(BaseWorker):
    def run(self) -> Dict[str, Any]:
        try:
            self.logger.info('slicer', 'Running slicer (placeholder)')
            self.sig_log.emit('Slicer: placeholder')
        except Exception:
            pass
        res = {'status': 'ok', 'stage': 'slicer'}
        try:
            self.sig_finished.emit(res)
        except Exception:
            pass
        return res
