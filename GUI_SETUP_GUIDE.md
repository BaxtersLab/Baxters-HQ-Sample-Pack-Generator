# GUI Setup and Testing Guide

## ✅ What's Been Completed

### 1. Virtual Environment Setup
- Created Python virtual environment in `env/`
- Installed PySide6 6.11.0 (Qt6 GUI framework)
- Installed bspg package and dependencies (pydantic, rich)

### 2. System Dependencies
- Installed required X11/xcb libraries for Qt6 on Linux:
  - libxcb-cursor0
  - libxcb-xinerama0  
  - libxcb-icccm4
  - libxcb-image0
  - libxcb-keysyms1
  - libxcb-randr0
  - libxcb-render-util0
  - libxcb-shape0

### 3. Code Fixes Applied
- Fixed empty widget containers (instantiated TopLaneRunStatus and TopLaneFileIO)
- Disabled blocking terms overlay temporarily
- Added error logging
- Fixed pyproject.toml format issues

## 🚀 How to Test the GUI

### Method 1: Using the test script

```bash
cd "/home/baxter/Desktop/workspace/Baxters HQ Sample Pack Generator"
chmod +x test_gui.sh
./test_gui.sh
```

### Method 2: Manual activation

```bash
cd "/home/baxter/Desktop/workspace/Baxters HQ Sample Pack Generator"
source env/bin/activate
python run_gui.py
```

### Method 3: Direct Python execution

```bash
cd "/home/baxter/Desktop/workspace/Baxters HQ Sample Pack Generator"
env/bin/python run_gui.py
```

## 🐛 Expected GUI Issues to Address

Based on the code audit, here are known issues that may still exist:

### 1. **Missing hqspg Package**
- The GUI imports from `hqspg._version` and `hqspg` module
- This package may need to be installed separately
- **Fix**: `pip install -e ./hqspg` (if it has a setup.py/pyproject.toml)

### 2. **Missing Flowchart Implementation**
- The flowchart container currently shows only placeholder text
- No actual pipeline visualization yet

### 3. **Debug Terminal Integration**
- May fail to import `bspg.gui.debug_terminal.debug_terminal_widget`
- Should not block GUI startup (errors are caught)

### 4. **Settings Panel**
- SettingsWindow import may fail
- Should not block GUI startup (errors are logged now)

### 5. **Platform-Specific Issues**
- Window may not have proper transparency/rounding on Linux X11
- Frameless window hint may behave differently than Windows

## 📋 Diagnostic Checklist

When you run the GUI, check for:

1. **Window Appears**
   - ✅ Window opens with proper size (800x600 minimum)
   - ✅ Window title shows "Baxters Sample Pack Generator"

2. **Top Lanes Visible**
   - ✅ "Run" button
   - ✅ "Settings" button  
   - ✅ "Debug" button
   - ✅ "Input File(s)" button
   - ✅ "Output Folder" button
   - ✅ HRT status indicator

3. **Middle Section**
   - ⚠️ Should show placeholder text: "Flowchart/Pipeline visualization will appear here"

4. **Debug Terminal**
   - ✅ Debug log area visible at bottom
   - Shows startup messages

## 🔧 Troubleshooting Commands

### Check if hqspg needs installation:
```bash
cd "/home/baxter/Desktop/workspace/Baxters HQ Sample Pack Generator"
source env/bin/activate
python -c "from hqspg._version import __product_name__; print(__product_name__)"
```

If it fails, install hqspg:
```bash
# Check if hqspg has a setup file
ls -la hqspg/setup.py hqspg/pyproject.toml

# If found, install it:
pip install -e ./hqspg
```

###Check imports:
```bash
source env/bin/activate
python -c "
from bspg.gui.main_window import MainWindow
from bspg.gui.logic.gui_controller import GUIController
from bspg.gui.top_lanes.lane1_run_status import TopLaneRunStatus
from bspg.gui.top_lanes.lane2_file_io import TopLaneFileIO
print('All core imports OK')
"
```

### Test PySide6:
```bash
source env/bin/activate
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
```

### View diagnostic output:
```bash
source env/bin/activate
python run_gui.py 2>&1 | tee gui_startup.log
```

## 📝 What to Report

If the GUI still doesn't work, please share:

1. **Console output** - Full output from `python run_gui.py`
2. **Screenshot** - If window appears but looks wrong
3. **Errors** - Any Python tracebacks or Qt errors
4. **Import test results** - Output from the import check above

## 🎯 Next Steps for Full Functionality

After the GUI displays:

1. **Accept legal terms** (if re-enabled)
   ```bash
   python tools/accept_terms.py
   ```

2. **Install hqspg package** if not already done

3. **Implement flowchart widgets** - Add actual pipeline visualization

4. **Test all buttons** - Verify Run, Settings, Debug, File I/O work

5. **Add backend integration** - Connect to actual audio processing pipeline

## 📖 Additional Resources

- **GUI_AUDIT_REPORT.md** - Complete analysis of GUI issues found and fixed
- **TROUBLESHOOTING.md** - Debugging guide for common issues
- **DEV_NOTE_FOR_AGENT.md** - Original developer notes about Windows issues

---

**Status**: Ready for testing ✅  
**Environment**: Linux with PySide6 6.11.0  
**Python**: 3.12.3  
**Location**: `/home/baxter/Desktop/workspace/Baxters HQ Sample Pack Generator`
