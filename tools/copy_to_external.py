import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = r"D:\vens_project"
EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'demucs_out', 'demucs_out_6s', 'test_output', '.pytest_cache', 'venv', 'node_modules'}
EXCLUDE_FILES_SUFFIX = ('.pyc', '.pyo')
EXCLUDE_FILES = {'diag_window.png', 'vens_project.tar.gz'}

copied = 0
errors = []

if not os.path.exists(DEST):
    try:
        os.makedirs(DEST)
    except Exception as e:
        print('Failed to create destination:', DEST, e)
        sys.exit(1)

for root, dirs, files in os.walk(ROOT):
    # compute relative path
    rel = os.path.relpath(root, ROOT)
    if rel == '.':
        rel = ''
    # filter dirs
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    # create destination dir
    dest_dir = os.path.join(DEST, rel) if rel else DEST
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
        except Exception as e:
            errors.append(('mkdir', dest_dir, str(e)))
            continue
    for f in files:
        if f in EXCLUDE_FILES:
            continue
        if f.endswith(EXCLUDE_FILES_SUFFIX):
            continue
        # skip requirements if large? keep it
        src = os.path.join(root, f)
        dst = os.path.join(dest_dir, f)
        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception as e:
            errors.append((src, dst, str(e)))

print('Copy complete. Files copied:', copied)
if errors:
    print('Errors (first 20):')
    for e in errors[:20]:
        print(e)
else:
    print('No errors')
