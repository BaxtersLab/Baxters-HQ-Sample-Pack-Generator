from PySide6.QtCore import QObject, Signal
from PySide6.QtCore import QThreadPool
from .workers import Worker, FullPipelineWorker, SeparateWorker, RepairWorker, ExtractWorker, ExportWorker
from .log import setup_gui_logger

import hqspg.pipeline as pipeline
import hqspg.separator as separator_mod
import hqspg.repair as repair_mod
import hqspg.extract as extract_mod
import hqspg.loader as loader_mod

logger = setup_gui_logger()


class Controller(QObject):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)
    status = Signal(str)
    log = Signal(str)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool.globalInstance()

    def run_full_pipeline(self, input_path: str, config: dict = None, output_base: str = None):
        """Run the full pipeline for a single input file in a worker thread."""
        logger.info('Controller: starting full pipeline for %s', input_path)
        self.status.emit('Starting full pipeline')
        w = FullPipelineWorker(input_path, config=config or {}, output_base=output_base)
        w.signals.progress.connect(self.progress.emit)
        w.signals.log.connect(self.log.emit)
        w.signals.finished.connect(self._on_finished)
        w.signals.error.connect(self._on_error)
        self.pool.start(w)

    def run_separate(self, file: str, out_dir: str = None, model: str = None, config: dict = None):
        logger.info('Controller: run separate %s', file)
        self.status.emit('Starting separation')
        w = SeparateWorker(file, out_dir=out_dir, model=model, config=config or {})
        w.signals.progress.connect(self.progress.emit)
        w.signals.log.connect(self.log.emit)
        w.signals.finished.connect(self._on_finished)
        w.signals.error.connect(self._on_error)
        self.pool.start(w)

    def run_repair(self, stem_dir: str, output_base: str = None, config: dict = None, track_name: str = None):
        logger.info('Controller: run repair on %s', stem_dir)
        # collect stems from folder
        import os
        stems = {}
        for fname in os.listdir(stem_dir):
            if fname.lower().endswith('.wav'):
                stem = os.path.splitext(fname)[0]
                stems[stem] = os.path.abspath(os.path.join(stem_dir, fname))
        self.status.emit('Starting repair')
        w = RepairWorker(stems, output_base=output_base, track_name=track_name, config=config or {})
        w.signals.progress.connect(self.progress.emit)
        w.signals.log.connect(self.log.emit)
        w.signals.finished.connect(self._on_finished)
        w.signals.error.connect(self._on_error)
        self.pool.start(w)

    def run_extract(self, stem_dir: str, output_base: str = None, track_name: str = None, config: dict = None):
        logger.info('Controller: run extract on %s', stem_dir)
        import os
        stems = {}
        for fname in os.listdir(stem_dir):
            if fname.lower().endswith('.wav'):
                stem = os.path.splitext(fname)[0]
                # strip _repaired suffix if present
                if stem.endswith('_repaired'):
                    stem = stem[:-9]
                stems[stem] = os.path.abspath(os.path.join(stem_dir, fname))
        self.status.emit('Starting extract')
        w = ExtractWorker(stems, output_base=output_base, track_name=track_name, config=config or {})
        w.signals.progress.connect(self.progress.emit)
        w.signals.log.connect(self.log.emit)
        w.signals.finished.connect(self._on_finished)
        w.signals.error.connect(self._on_error)
        self.pool.start(w)

    def load_input(self, path: str):
        """Synchronous input loader wrapper. Returns list of resolved files."""
        try:
            import os
            if os.path.isfile(path):
                files = loader_mod.load_input(mode='Single File', file=path, config=None)
            elif os.path.isdir(path):
                files = loader_mod.load_input(mode='Folder', folder=path, config=None)
            else:
                files = []
            self.log.emit(f'Loaded {len(files)} input(s)')
            return files
        except Exception as e:
            logger.exception('Failed to load input: %s', e)
            self.error.emit(str(e))
            return []

    def save_output(self, path: str):
        self._output_base = path
        self.log.emit(f'Set output base: {path}')

    def export_output(self, source_dir: str, dest_dir: str):
        try:
            self.status.emit('Starting export')
            w = ExportWorker(source_dir, dest_dir)
            w.signals.log.connect(self.log.emit)
            w.signals.progress.connect(self.progress.emit)
            w.signals.finished.connect(self._on_finished)
            w.signals.error.connect(self._on_error)
            self.pool.start(w)
        except Exception as e:
            logger.exception('Export failed: %s', e)
            self.error.emit(str(e))

    def run_randomize(self):
        # Randomize action removed — no-op kept for API compatibility
        try:
            self.log.emit('Randomize: removed in UI')
            self.finished.emit({'randomize': 'removed'})
        except Exception as e:
            self.error.emit(str(e))

    def start_demo_logs(self, n: int = 20, min_interval: float = 0.5, max_interval: float = 1.0):
        """Start a demo log QRunnable in the shared threadpool."""
        try:
            worker = DemoLogWorker(n=n, min_interval=min_interval, max_interval=max_interval)
            worker.signals.log.connect(self.log.emit)
            # forward demo finished to controller finished for UI convenience
            worker.signals.finished.connect(lambda: self.finished.emit({'demo': 'finished'}))
            self.pool.start(worker)
            logger.info('Controller: started demo logs (n=%s)', n)
        except Exception as e:
            logger.exception('Failed to start demo logs: %s', e)
            self.error.emit(str(e))

    def _on_finished(self, result):
        logger.info('Controller: finished')
        self.status.emit('Finished')
        self.finished.emit(result)

    def _on_error(self, err):
        logger.error('Controller error: %s', err)
        self.status.emit('Error')
        self.error.emit(err)
