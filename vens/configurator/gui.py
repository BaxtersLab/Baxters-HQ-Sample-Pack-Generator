import os
import sys
import subprocess
import threading
import json
from pathlib import Path

from PyQt5 import QtWidgets, QtCore

import requests
import yaml

ROOT = Path(__file__).resolve().parents[3]
# default paths (workspace-relative, but can be overridden)
SWITCH_SCRIPT = Path(r"c:\Users\Baxter\Desktop\gguf chatbox\tools\switch_continue_profile.py")
CONFIG_PATH = Path(r"C:\Users\Baxter\.continue\config.yaml")


def ensure_backups_dir(cfg_path: Path) -> Path:
    home = cfg_path.parent
    backups = home.joinpath("backups")
    backups.mkdir(parents=True, exist_ok=True)
    return backups


def backup_config(cfg_path: Path) -> Path:
    backups = ensure_backups_dir(cfg_path)
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backups.joinpath(f"config.yaml.{ts}")
    try:
        with cfg_path.open("r", encoding="utf-8") as src, dest.open("w", encoding="utf-8") as dst:
            dst.write(src.read())
        return dest
    except Exception:
        return None


def apply_profile(profile_name, cfg_path: Path = CONFIG_PATH, switch_script: Path = SWITCH_SCRIPT):
    """Backup config, then call switch helper to atomically apply profile."""
    if not cfg_path.exists():
        return False, f"config not found: {cfg_path}"
    # create backup
    bak = backup_config(cfg_path)
    if not bak:
        return False, "failed to create backup"

    cmd = [sys.executable, str(switch_script), "--config", str(cfg_path), "--profile", profile_name]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, p.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, (e.stderr or str(e))


def test_model_endpoint(api_base: str = "http://127.0.0.1:8080", expected_model: str = None):
    """Check /v1/models and a minimal chat completion. Return structured result."""
    out = {"ok": False, "models": None, "chat_ok": False, "model_match": None, "error": None}
    try:
        r = requests.get(f"{api_base}/v1/models", timeout=5)
        if r.ok:
            try:
                out["models"] = r.json()
            except Exception:
                out["models"] = r.text
    except Exception as e:
        out["error"] = f"models check failed: {e}"

    # Minimal chat completion; send empty model field to let server choose default
    try:
        payload = {"model": "", "messages": [{"role": "user", "content": "ping"}]}
        r = requests.post(f"{api_base}/v1/chat/completions", json=payload, timeout=15)
        if r.ok:
            out["chat_ok"] = True
            try:
                out["chat_response"] = r.json()
            except Exception:
                out["chat_response"] = r.text
    except Exception as e:
        out["error"] = (out.get("error") or "") + f"; chat test failed: {e}"

    # If expected_model provided, check presence in model listing or response
    if expected_model and out.get("models"):
        try:
            # models may be dict/list - do a substring search in JSON dump
            j = json.dumps(out["models"]) if not isinstance(out["models"], str) else out["models"]
            out["model_match"] = expected_model in j
        except Exception:
            out["model_match"] = None

    out["ok"] = bool(out.get("models") or out.get("chat_ok"))
    return out


class ConfiguratorWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model Configurator")
        self.resize(700, 420)
        layout = QtWidgets.QVBoxLayout()

        # Profile list and controls
        self.profile_list = QtWidgets.QListWidget()
        layout.addWidget(self.profile_list)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_apply = QtWidgets.QPushButton("Apply Selected Profile")
        self.btn_test = QtWidgets.QPushButton("Test Server")
        self.btn_refresh = QtWidgets.QPushButton("Refresh Profiles")
        self.btn_wipe = QtWidgets.QPushButton("Wipe MCP Memory")
        btn_row.addWidget(self.btn_apply)
        btn_row.addWidget(self.btn_test)
        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_wipe)
        layout.addLayout(btn_row)

        # MCP memory checkbox
        cb_row = QtWidgets.QHBoxLayout()
        self.chk_mcp = QtWidgets.QCheckBox("Create MCP memory file on apply")
        cb_row.addWidget(self.chk_mcp)
        cb_row.addStretch()
        layout.addLayout(cb_row)

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)

        self.btn_apply.clicked.connect(self.on_apply)
        self.btn_test.clicked.connect(self.on_test)
        self.btn_refresh.clicked.connect(self.load_profiles)
        self.btn_wipe.clicked.connect(self.on_wipe_memory)

        # Add create new profile button
        self.btn_create = QtWidgets.QPushButton("Create New Profile")
        btn_row.addWidget(self.btn_create)
        self.btn_create.clicked.connect(self.on_create)

        self.load_profiles()

    def log_line(self, s: str):
        # Schedule GUI update on the main thread to avoid queued-argument errors
        try:
            QtCore.QTimer.singleShot(0, lambda: self.log.append(s))
        except Exception:
            # Fallback: direct append (best-effort)
            try:
                self.log.append(s)
            except Exception:
                pass

    def load_profiles(self):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
            profiles = cfg.get('profiles', {})
            self.profile_list.clear()
            for name in profiles.keys():
                self.profile_list.addItem(name)
            self.log_line(f"Loaded {len(profiles)} profiles from config.")
        except Exception as e:
            self.log_line(f"Failed to load profiles: {e}")

    def on_apply(self):
        item = self.profile_list.currentItem()
        if not item:
            self.log_line("Select a profile first.")
            return
        name = item.text()
        self.log_line(f"Applying profile: {name}")
        self.btn_apply.setEnabled(False)

        def t():
            # Backup + apply (optionally create MCP memory file)
            try:
                mcp_flag = bool(self.chk_mcp.isChecked())
            except Exception:
                mcp_flag = False
            ok, out = apply_profile(name, cfg_path=CONFIG_PATH, switch_script=SWITCH_SCRIPT) if not mcp_flag else apply_profile(name, cfg_path=CONFIG_PATH, switch_script=SWITCH_SCRIPT)
            # If mcp flag set, call switch script with flag by invoking apply_profile below
            if mcp_flag:
                # rebuild cmd to add flag
                cmd = [sys.executable, str(SWITCH_SCRIPT), "--config", str(CONFIG_PATH), "--profile", name, "--mcp-memory"]
                try:
                    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    ok = True
                    out = p.stdout.strip()
                except subprocess.CalledProcessError as e:
                    ok = False
                    out = e.stderr or str(e)

            self.btn_apply.setEnabled(True)
            # Schedule GUI updates back on main thread
            QtCore.QTimer.singleShot(0, lambda: self.btn_apply.setEnabled(True))
            if ok:
                QtCore.QTimer.singleShot(0, lambda: self.log_line(f"Applied profile {name}. Output: {out}"))
            else:
                QtCore.QTimer.singleShot(0, lambda: self.log_line(f"Failed to apply profile {name}: {out}"))

        threading.Thread(target=t, daemon=True).start()

    def on_test(self):
        self.log_line("Testing local server…")
        self.btn_test.setEnabled(False)

        def t():
            # Use selected profile's apiBase/model if available
            item = self.profile_list.currentItem()
            api_base = "http://127.0.0.1:8080"
            expected_model = None
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                if item:
                    prof = cfg.get('profiles', {}).get(item.text(), {})
                    api_base = prof.get('apiBase', api_base)
                    expected_model = prof.get('model')
            except Exception:
                pass

            res = test_model_endpoint(api_base=api_base, expected_model=expected_model)
            # Schedule GUI updates on main thread
            QtCore.QTimer.singleShot(0, lambda: self.btn_test.setEnabled(True))
            QtCore.QTimer.singleShot(0, lambda: self.log_line(json.dumps(res, indent=2)))

        threading.Thread(target=t, daemon=True).start()

    def on_create(self):
        # Simple dialog to create a new profile
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle('Create New Profile')
        form = QtWidgets.QFormLayout(dlg)
        name_in = QtWidgets.QLineEdit()
        api_in = QtWidgets.QLineEdit()
        model_in = QtWidgets.QLineEdit()
        context_in = QtWidgets.QPlainTextEdit()
        context_in.setPlaceholderText('YAML block for `context` (optional)')
        form.addRow('Profile name:', name_in)
        form.addRow('apiBase:', api_in)
        form.addRow('model:', model_in)
        form.addRow('context (yaml):', context_in)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        def on_ok():
            name = name_in.text().strip()
            api = api_in.text().strip()
            model = model_in.text().strip()
            context_text = context_in.toPlainText().strip()
            if not name:
                QtWidgets.QMessageBox.warning(self, 'Missing', 'Profile name required')
                return
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
            except Exception as e:
                cfg = {}
            if 'profiles' not in cfg or cfg['profiles'] is None:
                cfg['profiles'] = {}
            profile_entry = {'provider': 'openai', 'apiBase': api or 'http://127.0.0.1:8080', 'apiKey': '', 'model': model or ''}
            if context_text:
                try:
                    profile_entry['context'] = yaml.safe_load(context_text)
                except Exception:
                    profile_entry['context'] = {'raw': context_text}
            cfg['profiles'][name] = profile_entry
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                yaml.safe_dump(cfg, f, sort_keys=False)
            dlg.accept()
            self.load_profiles()

        btns.accepted.connect(on_ok)
        btns.rejected.connect(dlg.reject)
        dlg.exec_()

    def on_wipe_memory(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirm Wipe', 'Delete all MCP memory files in memories/repo? This cannot be undone.',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply != QtWidgets.QMessageBox.Yes:
            return
        self.log_line('Wiping MCP memory...')
        self.btn_wipe.setEnabled(False)

        def t():
            try:
                adapter_path = Path(r"c:\Users\Baxter\Desktop\Vens Constitution\vens")
                if str(adapter_path) not in __import__('sys').path:
                    __import__('sys').path.insert(0, str(adapter_path))
                from vens.mempalace_adapter import wipe_memories
                removed = wipe_memories()
                self.log_line(f"Wipe complete. Removed {removed} items.")
            except Exception as e:
                self.log_line(f"Wipe failed: {e}")
            finally:
                QtCore.QTimer.singleShot(0, lambda: self.btn_wipe.setEnabled(True))

        threading.Thread(target=t, daemon=True).start()


def main():
    if QtWidgets is None:
        print("PyQt5 not available. Run `pip install PyQt5` to enable GUI.")
        print("You can still call the module's functions programmatically.")
        return
    app = QtWidgets.QApplication(sys.argv)
    w = ConfiguratorWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
