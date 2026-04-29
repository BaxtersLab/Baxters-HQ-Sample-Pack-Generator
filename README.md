# HQSPG — HQ Sample Pack Generator

This repository contains HQSPG: a pipeline to separate stems (Demucs), repair audio artifacts (HQ_StemRepair), and extract sample slices.

Installation

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

GUI Usage

- Launch the GUI:

```bash
python -m gui.main
```

- Use `Load` to pick a file or folder, `Save` to choose output folder.
- Tweak `silence` and `transient` controls on the top bar.
- Click `Generate` to run the full pipeline. Open the `Debug Terminal` drawer for live logs. Use `Demo Logs` to test logging without running the pipeline.

CLI Usage

- The `hqspg` package provides a CLI scaffold. For quick runs, use the `hqspg.pipeline.full_pipeline()` function in Python scripts.

Outputs

- Outputs are written to `<output_base>/<track_name>/` with subfolders:
  - `stems/` — raw separator outputs
  - `repaired/` — repaired stems
  - `samples/` — extracted slices per stem and `samples_manifest.json`

Resume & checkpoints

- Runs write to a temporary directory named `.hqspg_tmp_<track>_<ts>` under the output base.
- A `hqspg_state.json` file is written after each stage so runs can resume if interrupted. The GUI prefers resuming existing `.hqspg_tmp_<track>_*` folders.

Packaging

- A GitHub Actions workflow is provided at `.github/workflows/build_windows.yml` that uses `pyinstaller` to build a single EXE.

## About HQSPG

HQSPG (High-Quality Sample Pack Generator) is a multi-stage audio pipeline that performs:

- Source separation using Demucs
- Repair and artifact reduction using an optional repair/generative stage
- Silence-aware slicing and sample export for content creation

The project focuses on reproducible, high-fidelity results suitable for archival and creative reuse.

## Legal Responsibility Disclaimer

This software is provided as a research / tooling aid. Users are responsible for ensuring they have the legal right to process, deconstruct, or redistribute any audio they run through this pipeline. The authors accept no liability for infringement resulting from users' actions. When using the pipeline on copyrighted material, obtain necessary permissions or ensure your use qualifies as fair use under applicable law.

## License

This project is released under the MIT License — see the `LICENSE` file for details.

