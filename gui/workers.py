from PySide6.QtCore import QObject, Signal, QRunnable
import traceback
import logging


class WorkerSignals(QObject):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)
    log = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            # allow fn to accept a progress callback
            # install a temporary logging handler to forward logs to the UI
            logger = logging.getLogger()
            class SignalHandler(logging.Handler):
                def __init__(self, emit_fn):
                    super().__init__()
                    self.emit_fn = emit_fn
                def emit(self, record):
                    try:
                        msg = self.format(record)
                        self.emit_fn(msg)
                    except Exception:
                        pass

            handler = SignalHandler(self.signals.log.emit)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            res = self.fn(*self.args, **self.kwargs)
            # remove handler
            try:
                logger.removeHandler(handler)
            except Exception:
                pass
            self.signals.finished.emit(res)
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.error.emit(f"{e}\n{tb}")


# Specialized workers that call the HQSPG backend and emit progress/logs
class FullPipelineWorker(QRunnable):
    def __init__(self, input_path: str, config: dict = None, output_base: str = None):
        super().__init__()
        self.input_path = input_path
        self.config = config or {}
        self.output_base = output_base
        self.signals = WorkerSignals()

    def run(self):
        import logging, os, time, json, shutil
        logger = logging.getLogger(__name__)
        try:
            from hqspg.separator import separate
            from hqspg.repair import repair_stems
            from hqspg.extract import extract

            track_name = os.path.splitext(os.path.basename(self.input_path))[0]
            out_base = self.output_base or os.getcwd()
            # write into a temp run directory
            # prefer resuming an existing tmp run if present
            tmp_parent = out_base
            existing = None
            try:
                for name in sorted(os.listdir(tmp_parent)):
                    if name.startswith(f".hqspg_tmp_{track_name}_"):
                        existing = os.path.join(tmp_parent, name)
                        break
            except Exception:
                existing = None

            if existing and os.path.isdir(existing):
                tmp_dir = existing
            else:
                tmp_dir = os.path.join(out_base, f".hqspg_tmp_{track_name}_{int(time.time())}")
                os.makedirs(tmp_dir, exist_ok=True)
            state_path = os.path.join(tmp_dir, 'hqspg_state.json')
            state = {}
            if os.path.exists(state_path):
                try:
                    with open(state_path, 'r', encoding='utf-8') as sf:
                        state = json.load(sf)
                except Exception:
                    state = {}

            self.signals.log.emit(f'Starting full pipeline for {self.input_path} (tmp={tmp_dir})')

            # Stage 1: separate
            if not state.get('separated'):
                self.signals.log.emit('Running separator...')
                self.signals.progress.emit(5)
                stems = separate(self.input_path, out_dir=tmp_dir, model=(self.config or {}).get('separator', {}).get('model'))
                if isinstance(stems, dict) and stems.get('error'):
                    raise RuntimeError(f"Separator failed: {stems.get('error')}")
                state['separated'] = True
                state['stems'] = stems
                with open(state_path, 'w', encoding='utf-8') as sf:
                    json.dump(state, sf)
                self.signals.progress.emit(25)
                self.signals.log.emit('Separator finished')
            else:
                stems = state.get('stems', {})
                self.signals.log.emit('Separator already completed; resuming')
                self.signals.progress.emit(25)

            # Stage 2: repair
            if not state.get('repaired'):
                self.signals.log.emit('Running repair...')
                self.signals.progress.emit(35)
                repaired = repair_stems(stems, output_base=tmp_dir, track_name=track_name, config=(self.config or {}).get('repair', {}))
                state['repaired'] = True
                state['repaired_info'] = repaired
                with open(state_path, 'w', encoding='utf-8') as sf:
                    json.dump(state, sf)
                self.signals.progress.emit(65)
                self.signals.log.emit('Repair finished')
            else:
                repaired = state.get('repaired_info', {})
                self.signals.log.emit('Repair already completed; resuming')
                self.signals.progress.emit(65)

            # gather repaired paths
            repaired_paths = {s: v.get('repaired_path') for s, v in (repaired or {}).items() if isinstance(v, dict) and v.get('repaired_path')}

            # Stage 3: extract
            if repaired_paths and not state.get('extracted'):
                self.signals.log.emit('Running extractor...')
                self.signals.progress.emit(70)
                slices = extract(repaired_paths, output_base=tmp_dir, track_name=track_name, config=(self.config or {}).get('extractor', {}))
                state['extracted'] = True
                state['slices'] = slices
                with open(state_path, 'w', encoding='utf-8') as sf:
                    json.dump(state, sf)
                self.signals.progress.emit(90)
                self.signals.log.emit('Extraction finished')
            else:
                slices = state.get('slices', [])
                if not repaired_paths:
                    self.signals.log.emit('No repaired paths found; skipping extraction')

            # finalize: move tmp_dir -> final dir atomically (rename preferred)
            final_dir = os.path.join(out_base, track_name)
            try:
                if os.path.exists(final_dir):
                    self.signals.log.emit(f'Removing existing final dir {final_dir}')
                    shutil.rmtree(final_dir)
                # attempt atomic rename
                os.rename(tmp_dir, final_dir)
            except OSError:
                # fallback for cross-filesystem: copy -> verify -> remove
                self.signals.log.emit('Atomic rename failed; falling back to copy-and-replace')
                try:
                    shutil.copytree(tmp_dir, final_dir)
                    # basic verification: ensure manifest exists or at least files copied
                    if not os.path.exists(final_dir):
                        raise RuntimeError('Copy failed')
                    # remove tmp
                    shutil.rmtree(tmp_dir)
                except Exception as e:
                    self.signals.log.emit(f'Fallback copy failed: {e}')
                    raise
            self.signals.progress.emit(100)
            self.signals.log.emit(f'Pipeline completed; outputs at {final_dir}')
            self.signals.finished.emit({'output': final_dir, 'slices': slices})
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.log.emit(f'Error in full pipeline: {e}')
            self.signals.error.emit(f"{e}\n{tb}")


class SeparateWorker(QRunnable):
    def __init__(self, input_path: str, out_dir: str = None, model: str = None, config: dict = None):
        super().__init__()
        self.input_path = input_path
        self.out_dir = out_dir
        self.model = model
        self.config = config or {}
        self.signals = WorkerSignals()

    def run(self):
        try:
            from hqspg.separator import separate
            self.signals.log.emit(f'Starting separation for {self.input_path}')
            self.signals.progress.emit(10)
            mapping = separate(self.input_path, out_dir=self.out_dir, model=self.model, config=self.config)
            self.signals.progress.emit(60)
            self.signals.log.emit('Separation finished')
            self.signals.finished.emit(mapping)
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.log.emit(f'Error in separation: {e}')
            self.signals.error.emit(f"{e}\n{tb}")


class RepairWorker(QRunnable):
    def __init__(self, stems: dict, output_base: str = None, track_name: str = None, config: dict = None):
        super().__init__()
        self.stems = stems
        self.output_base = output_base
        self.track_name = track_name
        self.config = config or {}
        self.signals = WorkerSignals()

    def run(self):
        try:
            from hqspg.repair import repair_stems
            self.signals.log.emit('Starting repair')
            self.signals.progress.emit(10)
            results = repair_stems(self.stems, output_base=self.output_base, track_name=self.track_name, config=self.config)
            self.signals.progress.emit(80)
            self.signals.log.emit('Repair finished')
            self.signals.finished.emit(results)
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.log.emit(f'Error in repair: {e}')
            self.signals.error.emit(f"{e}\n{tb}")


class ExtractWorker(QRunnable):
    def __init__(self, stems: dict, output_base: str = None, track_name: str = None, config: dict = None):
        super().__init__()
        self.stems = stems
        self.output_base = output_base
        self.track_name = track_name
        self.config = config or {}
        self.signals = WorkerSignals()

    def run(self):
        try:
            from hqspg.extract import extract
            self.signals.log.emit('Starting extraction')
            self.signals.progress.emit(10)
            slices = extract(self.stems, output_base=self.output_base, track_name=self.track_name, config=self.config)
            self.signals.progress.emit(100)
            self.signals.log.emit('Extraction finished')
            self.signals.finished.emit(slices)
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.log.emit(f'Error in extraction: {e}')
            self.signals.error.emit(f"{e}\n{tb}")


class ExportWorker(QRunnable):
    def __init__(self, source_dir: str, dest_dir: str):
        super().__init__()
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.signals = WorkerSignals()

    def run(self):
        try:
            import shutil, os
            self.signals.log.emit(f'Exporting from {self.source_dir} to {self.dest_dir}')
            if not os.path.isdir(self.source_dir):
                raise FileNotFoundError(self.source_dir)
            os.makedirs(self.dest_dir, exist_ok=True)
            # simple copytree-like behavior for contents
            for item in os.listdir(self.source_dir):
                s = os.path.join(self.source_dir, item)
                d = os.path.join(self.dest_dir, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            self.signals.log.emit('Export complete')
            self.signals.finished.emit({'exported_to': self.dest_dir})
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.log.emit(f'Error in export: {e}')
            self.signals.error.emit(f"{e}\n{tb}")
