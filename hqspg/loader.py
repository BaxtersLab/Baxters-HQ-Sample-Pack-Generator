"""HQSPG loader module (scaffold)

Provides `HQLoader` which normalizes input file lists for the pipeline.
No DSP or heavy I/O is implemented in this scaffold; methods provide
signatures, docstrings, logging placeholders, and config hooks.
"""
from typing import List, Optional, Dict
import logging
import os

logger = logging.getLogger(__name__)


class HQLoader:
    """Batch input loader for HQSPG.

    Responsibilities:
    - Accept single file, folder, or explicit file list inputs
    - Validate file existence and basic audio file extensions
    - Return a deterministic list of input file paths for processing
    """

    def __init__(self, config: Optional[Dict] = None, logger_obj: Optional[logging.Logger] = None):
        self.config = config or {}
        if logger_obj is not None:
            self.logger = logger_obj
        else:
            self.logger = logger
        self.logger.debug("HQLoader initialized with config: %s", self.config)

    def validate_inputs(self, inputs: Dict) -> bool:
        """Validate provided input dict. Expected keys: mode, file/folder/files.

        Returns True if basic validation passes, False otherwise.
        """
        mode = inputs.get('mode')
        if mode not in ("Single File", "Folder", "Selected Files"):
            self.logger.error("Unsupported mode: %s", mode)
            return False
        # Additional lightweight checks
        return True

    def load(self, mode: str, file: Optional[str] = None, folder: Optional[str] = None, files: Optional[List[str]] = None) -> List[str]:
        """Return a normalized list of file paths based on `mode`.

        This is a scaffold: it performs minimal validation and returns
        file paths; no audio decoding is performed.
        """
        self.logger.info("Loading inputs mode=%s file=%s folder=%s files=%s", mode, file, folder, files)
        files = files or []
        result: List[str] = []
        if mode == "Single File":
            if file and os.path.isfile(file):
                result = [file]
            else:
                self.logger.warning("Single File mode but file missing: %s", file)
                result = []
        elif mode == "Folder":
            if folder and os.path.isdir(folder):
                found = []
                for entry in sorted(os.listdir(folder)):
                    if entry.lower().endswith('.wav'):
                        found.append(os.path.join(folder, entry))
                result = found
            else:
                self.logger.warning("Folder mode but folder missing: %s", folder)
                result = []
        else:
            # Selected Files
            valid = [p for p in files if os.path.isfile(p)]
            missing = [p for p in files if not os.path.isfile(p)]
            if missing:
                self.logger.warning("Some selected files missing: %s", missing)
            result = valid

        self.logger.debug("Loader returning %d files", len(result))
        return result


def load_input(mode: str = "Folder", file: Optional[str] = None, folder: Optional[str] = None, files: Optional[List[str]] = None, config: Optional[Dict] = None) -> List[str]:
    """Compatibility wrapper used by GUI controller.

    Returns a list of file paths resolved by HQLoader.
    """
    loader = HQLoader(config=config or {})
    return loader.load(mode=mode, file=file, folder=folder, files=files)
