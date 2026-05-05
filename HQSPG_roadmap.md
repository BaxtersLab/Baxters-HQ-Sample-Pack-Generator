# Baxter’s HQ Sample Pack Generator (HQSPG) — Development Roadmap

## 1. Title and Overview

Baxter’s HQ Sample Pack Generator (HQSPG) is a standalone application that automates the creation
of high‑quality sample packs from full mixes. HQSPG performs stem separation, automated stem repair,
and sample extraction to produce ready‑to‑use single‑hit samples and multi‑stem bundles for producers,
sound designers, and sample‑pack creators.

Purpose
- Provide a deterministic, high‑quality pipeline that transforms a song/mix into a collection of
  cleaned, normalized samples per stem, leveraging Demucs for separation and the HQ_StemRepair
  glimmer‑repair engine to remove transient artifacts.

Target users
- Electronic music producers and beatmakers
- Sound designers and sample pack authors
- Audio engineers looking for fast sample harvesting from source material

## 2. High‑Level Architecture

HQSPG implements a 3→4 stage sequential pipeline (designed intentionally sequential — no parallel
execution by default):

1. HQ_Loader — Batch input and file selection
   - Accepts single file, folder, or explicit file lists. Produces normalized file list for processing.

2. HQ_separator — Demucs integration
   - Runs `demucs` (recommended: `htdemucs_6s`) to generate stems.
   - Produces per‑track stems: `vocals`, `drums`, `bass`, `guitar`, `piano`, `other`.

3. HQ_StemRepair — Glimmer detection & repair
   - Detects short high‑frequency transient noise (glimmers) and repairs stems conservatively.
   - Two modes: `fast` (median spectral filtering) and `balanced` (FFT inpainting).

4. HQ_SampleExtractor — Silence slicing + transient detection
   - Detects events, aligns to zero‑crossing, trims/pads, applies fades/normalization,
     and outputs individual `*.wav` samples.

Sequential processing note
- Each stage runs after the previous completes; the process is intentionally sequential to
  simplify resource management and guarantee deterministic outputs.

Output folder structure and naming scheme
- Root output folder: `HQSPG_output/<source_basename>/`
  - `<song>_stems/` — raw demucs stems (original demucs outputs)
  - `<song>_repaired/` — repaired stems (per‑stem `*_repaired.wav`)
  - `<song>_samples/<stem>/` — individual sample files per stem
  - `<song>_samples/metadata/` — CSV/JSON manifest (origin, stem, start_ms, end_ms, rms, notes)

Naming convention for samples
- `<song>_<stem>_NNNN.wav` (zero‑padded sequence), e.g. `MidnightDrive_guitar_0001.wav`.
- Metadata file: `samples_manifest.json` with an array of sample objects.

## 3. Detailed Development Phases

### Phase 1 — Project Scaffolding (week 0–1)
- Create repository and top‑level folder structure:
  - `hqspg/` package, `cli.py`, `config/`, `tests/`, `docs/`, `examples/`.
- Create Python package layout with `pyproject.toml` (or `setup.cfg`) and basic `requirements.txt`.
- Implement CLI entry point `hqspg run --config config.yaml` with argument parsing (`argparse` or `typer`).
- Create configuration system (YAML config + config validator) containing model selection, thresholds,
  staging folders, and logging settings.
- Deliverables: skeleton package, CLI, config loader, unit test harness.

### Phase 2 — Core Pipeline Integration (week 1–3)
- Implement `HQ_Loader` module (batch ingestion, file list normalization, simple validation).
- Integrate `HQ_separator` via `demucs` invocation wrapper; implement safe subprocess call with
  fallback `python -m demucs` and clear error messages.
- Integrate `HQ_StemRepair` logic from existing ComfyUI node into a reusable library API.
- Implement the sequential batch loop: for each input file, run separator → repair → sample extraction
  (sample extraction stubbed until Phase 3).
- Deliverables: working end‑to‑end pipeline that produces repaired stems and writes a processing log.

### Phase 3 — Sample Extraction Engine (week 3–6)
- Implement robust silence detection (RMS envelope or spectral flux) with configurable `silence_threshold` and `min_silence_ms`.
- Implement transient detection (onset detection using spectral flux or energy) and event merging based on `min_event_ms`.
- Implement slicing logic with options: pad before/after events, merge close events, discard too short events.
- Implement normalization, optional RMS target, optional peak normalization, fades, and zero‑cross alignment.
- Create naming and indexing strategy: per‑song, per‑stem sequential numbering and deterministic ordering.
- Deliverables: sample extraction library functions and unit tests validating boundaries and naming.

### Phase 4 — Output System (week 6–7)
- Implement per‑track subfolder creation, safe file writes, and atomic move/rename patterns to avoid incomplete outputs.
- Implement relative output paths and optional per‑run work directories (temp → final move when complete).
- Implement logging and progress reporting (CLI progress bar and JSON log for each track). Support verbose and quiet modes.
- Deliverables: predictable output layout, manifest files, and CLI options for output path.

### Phase 5 — User Interface Options (week 7–9)
- Required: Full CLI mode with rich argument and configuration support (`typer` recommended).
- Optional: Lightweight GUI prototype (Tkinter or PySide6) to run single projects and show progress.
- Optional: Drag‑and‑drop watch folder mode for interactive use.
- Deliverables: CLI reference, optional GUI binary prototype.

### Phase 6 — Optimization & Stability (week 9–11)
- Memory management for large files: streaming reads, avoid full in‑memory copies where possible.
- Sequential GPU/CPU scheduling: allow Demucs to use GPU when available; ensure post‑processing runs on CPU.
- Robust error handling and recovery: checkpointing after each stage; resume partial runs without reprocessing finished stages.
- Implement retries for transient subprocess failures and clear user guidance for missing dependencies.
- Deliverables: resilience tests, long‑run validation dataset, and recovery documentation.

### Phase 7 — Packaging & Distribution (week 11–13)
- Create build scripts for `PyInstaller` (Windows EXE) and test `pip` installable package.
- Prepare release notes, versioning strategy (semantic versioning), and CHANGELOG.
- Optional: macOS bundle instructions or CI jobs for release artifacts.
- Deliverables: distributable artifact(s), installer instructions, and packaging CI pipeline.

## 4. Milestones & Deliverables

- Milestone A (end Phase 1): Project skeleton + CLI + config loader
- Milestone B (end Phase 2): End‑to‑end pipeline with Demucs and StemRepair integrated (repaired stems written)
- Milestone C (end Phase 3): Fully functional SampleExtractor with deterministic slicing and naming
- Milestone D (end Phase 4): Robust output system, manifest generation, and logging
- Milestone E (end Phase 5): CLI completed; optional GUI prototype
- Milestone F (end Phase 6): Stability and resume features validated
- Milestone G (end Phase 7): Packaged release candidate and documentation

For each milestone include:
- Code modules added or modified (e.g., `hqspg/loader.py`, `hqspg/separator.py`)
- Integration tests and unit tests
- Example outputs under `examples/` and `tests/data/`

## 5. Final Notes

- Sequential processing is a core design decision: it simplifies resource management,
  improves determinism, and reduces complexity of concurrent Demucs runs on single‑GPU machines.
- Portability: target pure‑Python dependencies where possible; document external native dependencies
  (Demucs, PyTorch) and provide packaging instructions for Windows users.
- HQSPG is envisioned as the flagship standalone product; the ComfyUI nodes are treated as
  companion integrations for in‑UI experimentation.
- Future expansion: a richer GUI, real‑time batch dashboards, more advanced SampleExtractor DSP
  (transient separation, pitch detection for sample categorization), and presets for genres.

---

If you want, I can now scaffold the `hqspg/` package and initial `pyproject.toml` and CLI entrypoint
so we can begin Phase 1 immediately. Otherwise I will mark this roadmap file complete.
