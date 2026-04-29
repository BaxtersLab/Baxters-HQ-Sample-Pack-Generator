**MemPalace MCP Integration Notes**

- **Purpose:** minimal adapter to export selected `profiles` from `C:\Users\Baxter\.continue\config.yaml` into MCP-style memory files so VS Code tooling (orchestrator/agents) can read exact, verbatim profile data.
- **Location:** `vens/mempalace_adapter` (lightweight wrapper that writes markdown files with YAML frontmatter).

Top-level `config.yaml` properties we support (minimal mapping):

- `name`, `version`, `schema`: kept as-is in `config.yaml` (not copied into memory file frontmatter).
- `models`: first entry is updated by `tools/switch_continue_profile.py` when applying a profile.
- `profiles`: named profiles stored in `config.yaml`; these are the source for MCP memory files.
- `context`: copied verbatim into the memory file body under YAML dump.
- `rules`, `prompts`, `docs`, `mcpServers`, `data`: preserved when present — adapter will include them in the memory file YAML body.

Memory file format (minimal):

1. YAML frontmatter with `profile` and `model` fields.
2. Markdown body with a YAML dump of the full profile dict.

Example generated `memories/repo/profile-Qwen3.5-9B.md`:

---
profile: Qwen3.5-9B
model: Qwen3.5-9B-GLM5.1-Distill-v1-BF16.gguf
---

# Profile memory

<YAML dump of the profile including `context`, `rules`, `prompts`, etc.>

Usage

- Apply a profile with MCP memory file via CLI:
```
python tools/switch_continue_profile.py --config "C:\Users\Baxter\.continue\config.yaml" --profile Qwen3.5-9B --mcp-memory
```
- Or run the GUI (`Vens Constitution\vens\orchestrator.bat`) and enable "Create MCP memory file on apply".

Notes & Constraints

- This is intentionally minimal: we do not import upstream search/index backends or run background indexing. The adapter only writes verbatim profile data to `memories/repo`.
- License: upstream MemPalace is MIT; we adapted a small, attributed subset.
- For heavier integrations (indexing, AAAK dialect, L0-L3 layers), keep upstream package in workspace and call its modules directly later.

Next steps (optional):
- Show last-written memory file path in the GUI after apply.
- Add a small `memories/repo/README.md` explaining retention and wipe policy.
# Config Notes — mechanical patch reference

Purpose
- Capture the exact steps and checks required to safely apply a model/profile to `C:\Users\Baxter\.continue\config.yaml` and verify the chatbox server is serving the selected model. These notes feed directly into the mechanical patch implementation.

Paths and artifacts
- Continue config: `C:\Users\Baxter\.continue\config.yaml`
- Switch helper: `C:\Users\Baxter\Desktop\gguf chatbox\tools\switch_continue_profile.py`
- Tauri backend: `C:\Users\Baxter\Desktop\gguf chatbox\src-tauri\src\main.rs` (contains `cmd_load_model`, `cmd_list_models`)
- GUI helper: `Vens Constitution\vens\configurator\gui.py`
- Backups folder: `C:\Users\Baxter\.continue\backups\`

Manual onboarding steps (to record during tests)
1. Ensure model file(s) are present in the chatbox models folder (e.g. `~/.gguf-chatbox/models/<name>.gguf`) or the app's model library.
2. Add a profile entry under `profiles` in `config.yaml` (name, provider, apiBase, apiKey, model).
3. Run the switch helper:
   ```
   python tools\switch_continue_profile.py --config "C:\Users\Baxter\.continue\config.yaml" --profile <ProfileName>
   ```
4. Restart or signal the chatbox server to reload models (if necessary). Options:
   - Restart the app that hosts the server.
   - Use a Tauri command (future): add a `cmd_reload_model` to `src-tauri` that reloads the currently referenced `models[0]`.
5. Verify server:
   - `curl -I http://127.0.0.1:8080/v1/models` (check for model listing)
   - POST a minimal chat completion to `/v1/chat/completions` and assert a valid JSON response.
6. If failure: restore backup and log failure details.

Mechanical patch algorithm (summary)
1. Preconditions: model file exists locally OR a known resolve URL is available.
2. Backup: copy `config.yaml` → `.continue/backups/config.yaml.YYYYMMDD_HHMMSS`
3. Apply: use `switch_continue_profile.py` to atomically set `models[0]` and `active_profile`.
4. Signal reload: invoke Tauri reload command or orchestrator hook; if not available, request user to restart server.
5. Verify: run tests (HEAD `/v1/models`, POST `/v1/chat/completions` with a minimal messages payload). Acceptable if either returns model info or a valid chat response.
6. Retry policy: try verification up to 3 times with backoff (e.g., 5s → 15s → 30s).
7. Rollback: if verification fails after retries, restore backup and emit a failure log.

Validation checks to implement
- Confirm `Content-Type` from remote downloads is not HTML/JSON (reject repo pages).
- Ensure `models[0].model` string matches served model id returned by the server (when available).
- Check file permissions and ownership before renaming `.part` → final.

Logging and telemetry
- Record one line per apply attempt: timestamp, profile, applied_by (GUI/CLI), server_endpoint, verification_result, error_message (if any), backup_path.
- Store logs in `C:\Users\Baxter\.continue\logs\apply.log` (append-only).

Testing matrix (manual before automation)
- New model downloads: perform 5 complete downloads and apply cycles, recording logs and backups.
- Existing profiles: apply 5 different existing profiles and verify server responds.

Implementation notes for the mechanical patch
- Language: Python (reuse `switch_continue_profile.py` and `requests` for HTTP checks).
- Atomic writes: leverage existing helper for models changes; use temp file + move for backups.
- Server signal: prefer a Tauri command (add `cmd_reload_model`) so the patch can call `tauri::AppHandle` event; otherwise orchestrator detection via filesystem is acceptable.
- Safety: always keep `.part` files and named backups on error; never delete without explicit user confirmation.

Example verification snippet (pseudo-Python)
```
def verify(api_base):
    try:
        r = requests.get(f"{api_base}/v1/models", timeout=5)
        if r.ok: return True
    except: pass
    try:
        r = requests.post(f"{api_base}/v1/chat/completions", json={"model":"","messages":[{"role":"user","content":"ping"}]}, timeout=10)
        return r.ok
    except: return False
```

Next steps
- Record 5 successful onboarding runs and 5 successful existing-profile activations (log each step to `config_notes.md` with timestamps and any deviations). Once satisfied, implement the mechanical patch script using this spec.
