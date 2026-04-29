import os
import sys
import tarfile
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_NAME = os.path.join(ROOT, 'vens_project.tar.gz')
EXCLUDES = [
    '.venv',
    '__pycache__',
    '.git',
    'demucs_out',
    'demucs_out_6s',
    'test_output',
    '.pytest_cache',
    'venv',
    'node_modules',
    '*.pyc',
    'diag_window.png',
]

def should_exclude(path):
    for ex in EXCLUDES:
        if ex.endswith('*'):
            if path.startswith(ex[:-1]):
                return True
        elif ex.startswith('*.'):
            if path.endswith(ex[1:]):
                return True
        else:
            # match directories or exact names
            parts = path.split(os.sep)
            if ex in parts:
                return True
            if path.startswith(ex + os.sep):
                return True
    return False

# generate requirements.txt
try:
    print('Generating requirements.txt...')
    req_path = os.path.join(ROOT, 'requirements.txt')
    with open(req_path, 'w', encoding='utf-8') as f:
        subprocess.check_call([sys.executable, '-m', 'pip', 'freeze'], stdout=f)
    print('Wrote', req_path)
except Exception as e:
    print('Failed to generate requirements.txt:', e)

# create DEV_NOTE_FOR_STRONGER_AGENT.md
note_path = os.path.join(ROOT, 'DEV_NOTE_FOR_STRONGER_AGENT.md')
note = f"""
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

"""
with open(note_path, 'w', encoding='utf-8') as f:
    f.write(note)
print('Wrote', note_path)

# create tar.gz
print('Creating archive', ARCHIVE_NAME)
with tarfile.open(ARCHIVE_NAME, 'w:gz') as tar:
    for root, dirs, files in os.walk(ROOT):
        # compute relative path
        rel_root = os.path.relpath(root, ROOT)
        if rel_root == '.':
            rel_root = ''
        # filter dirs in-place to avoid descending into excludes
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(rel_root, d))]
        for f in files:
            rel_path = os.path.join(rel_root, f) if rel_root else f
            if should_exclude(rel_path):
                continue
            fullpath = os.path.join(root, f)
            tar.add(fullpath, arcname=rel_path)
print('Archive created at', ARCHIVE_NAME)

# Attempt to detect removable drives and copy archive if found
try:
    import string
    import ctypes
    drives = []
    bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
    for d in range(26):
        if bitmask & (1 << d):
            drive = f"{string.ascii_uppercase[d]}:\\"
            if drive.startswith(('A:','B:')):
                continue
            # check drive type (2 = removable, 3 = local)
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            drives.append((drive, drive_type))
    removable = [d for d,t in drives if t==2]
    if removable:
        dest = os.path.join(removable[0], os.path.basename(ARCHIVE_NAME))
        print('Removable drive found:', removable[0], 'copying to', dest)
        shutil.copy2(ARCHIVE_NAME, dest)
        print('Copied archive to removable drive:', dest)
    else:
        print('No removable drive found. Archive remains in project root.')
except Exception as e:
    print('Drive detection/copy skipped:', e)

print('Done')
