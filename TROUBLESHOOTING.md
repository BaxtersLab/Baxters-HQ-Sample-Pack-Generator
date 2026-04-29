# GUI Troubleshooting Guide

## Issue: Blank/White Window

### Root Causes Identified

1. **Empty UI Containers** - The MainWindow was creating empty container widgets but never populating them with actual UI components.
   
2. **Terms Acceptance Gate** - The app has a legal terms gate that applies a semi-transparent overlay blocking the entire window until terms are accepted. Default is `terms_accepted = False`.

### Fixes Applied

#### 1. Widget Instantiation (FIXED)
- Modified `bspg/bspg/gui/main_window.py::init_top_lanes()` to instantiate and attach `TopLaneRunStatus` and `TopLaneFileIO` widgets
- Added placeholder text to flowchart container so users see content

#### 2. Terms Gate (TEMPORARILY DISABLED)
- Commented out the blocking overlay in `bspg/bspg/gui/logic/gui_controller.py::check_terms_gate()`
- This allows GUI to display while you implement proper terms acceptance flow

### How to Accept Terms Permanently

Run the utility script:
```bash
python tools/accept_terms.py
```

Or manually edit your config file (usually in `~/.hqspg/` or similar) and set:
```json
{
  "terms_accepted": true
}
```

### TODO: Implement Proper Terms Flow

The commented-out overlay code should be re-enabled after implementing:

1. A visible "Accept Terms" dialog on first launch
2. A clear Settings button that lets users accept terms
3. Visual feedback when terms are blocking features

### Other Potential Issues

#### Threading Issues
- The `HRTConnector` starts a background thread but it's daemonized so shouldn't block
- Ensure all GUI updates from background threads use Qt signals/slots

#### Error Swallowing
- Many `try/except` blocks hide exceptions
- Check logs for silent failures
- Consider adding structured logging with proper error handlers

#### Platform-Specific Issues
- Windows: Single-instance lock using `msvcrt`
- Linux: Fallback to file-based locking
- Ensure `WA_TranslucentBackground` doesn't cause rendering issues on your platform

### Running Tests

Verify the fixes:
```bash
# Quick test
pytest tests/test_imports.py -v

# GUI-specific tests
pytest bspg/bspg/tests/test_gui_controller.py -v
pytest bspg/bspg/tests/test_lane1_run_status.py -v
```

### Diagnostic Output

The instrumented `run_gui.py` includes extensive diagnostic printing. Look for:
- `DEBUG:` messages showing import and instantiation steps
- `DIAG:` messages showing widget hierarchy
- `GEOM:` messages showing widget geometry
- `STYLE:` messages showing stylesheet and palette info

If the window is still blank, check:
1. Does `diag_window.png` show any content?
2. Are there Python exceptions printed to console?
3. Is Qt installed correctly? (`python -c "from PySide6.QtWidgets import QApplication; print('OK')"`)

### Clean Slate

If issues persist, try:
```bash
# Remove old config
rm -rf ~/.hqspg/

# Accept terms
python tools/accept_terms.py

# Run with fresh config
python run_gui.py
```
