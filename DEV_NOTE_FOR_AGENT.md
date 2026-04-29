
Dev note for Linux audit — vens_project

Context:
- Issue: On Windows some users saw a persistent dead/gray window while the real Qt window was healthy.
- Repro: Diagnostics were run (geometry, style, palette, screenshot saved to diag_window.png).
- run_gui.py was instrumented for diagnostics (temporarily).

Files changed (temporary instrumentation):
- run_gui.py (added diagnostic blocks and screenshot capture)
- tools/inspect_windows.py (window enumerator)
- tools/package_for_external.py (this packaging script)
- diag_window.png (screenshot of the rendered UI)

What to audit first:
1. Reproduce on Linux (X11/Wayland) if possible, but primary focus is on code correctness:
   - Threading: ensure all background threads (hrt_connector) communicate via Qt-safe mechanisms (signals/slots or QTimer.singleShot) and do not call widget methods directly.
   - Error swallowing: many try/except blocks in `bspg/gui/main_window.py` hide exceptions — recommend adding structured logging and avoiding bare excepts.
   - Rendering: check custom widgets in `flowchart_container` for paintEvent exceptions.
   - Single-instance lock and startup path handling in `run_gui.py`.

How to run locally (recommended):

1. Create venv and install:
   python -m venv env
   source env/bin/activate
   pip install -r requirements.txt

2. Run the app:
   python run_gui.py

3. Run tests:
   pytest -q

Notes:
- I removed virtualenv and large outputs from the archive. Add any missing large model files separately.
- If you need to inspect the instrumented run_gui.py, it's included; I can revert the instrumentation after audit.

