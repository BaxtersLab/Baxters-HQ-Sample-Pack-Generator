import logging
from pathlib import Path
import shutil


class Stage3Slicer:
    """Simple placeholder slicer.

    For now this creates a numbered copy of the input WAV into the output
    folder so downstream wiring and tests can exercise the slicer without
    requiring heavy DSP dependencies. Real slicing logic can replace this
    implementation later.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def run(self, input_file: Path, out_folder: Path, base_name: str = "slice", count: int = 1):
        out_folder = Path(out_folder)
        out_folder.mkdir(parents=True, exist_ok=True)
        outputs = []
        for i in range(1, max(1, count) + 1):
            dest = out_folder / f"{base_name}_{i}{input_file.suffix}"
            shutil.copy2(input_file, dest)
            self.logger.info("Wrote slice: %s", dest)
            outputs.append(dest)
        return outputs
