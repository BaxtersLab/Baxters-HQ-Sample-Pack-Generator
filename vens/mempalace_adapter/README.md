MemPalace Minimal MCP Shim
==========================

This folder contains a minimal, offline MCP shim used to provide a safe, local-only
MCP server for Continue. The shim implements a tiny JSON-RPC-over-stdio loop and
is intended for testing and small-scale local workflows.

Files
- `mempalace_minimal_mcp.py` - the shim process. Reads JSON lines from stdin and
  writes JSON-RPC responses on stdout. Logs requests to `vens/onboarding-reports/mempalace_minimal.log`.

Why this exists
- The upstream `mempalace/` copy contains docs and integration code that may reference
  cloud services or heavy dependencies. The shim offers a lean, auditable MCP server
  with zero network calls.

Quarantine
- On 2026-04-18 a backup of `C:\Users\Baxter\Desktop\mempalace` was created at
  `vens/onboarding-reports/backups/mempalace-<timestamp>` and `CLAUDE.md` was moved to
  `C:\Users\Baxter\Desktop\mempalace\QUARANTINE\CLAUDE.md`.

Rollback commands
-- To restore quarantined file:

```
Move-Item -Path "C:\Users\Baxter\Desktop\mempalace\QUARANTINE\CLAUDE.md" -Destination "C:\Users\Baxter\Desktop\mempalace\CLAUDE.md" -Force
```

-- To restore the full backup copy (replace <timestamp> with the actual folder name):

```
Remove-Item -Recurse -Force C:\Users\Baxter\Desktop\mempalace
Move-Item -Path "vens\onboarding-reports\backups\mempalace-<timestamp>" -Destination "C:\Users\Baxter\Desktop\mempalace"
```

-- To remove the shim (if you change your mind):

```
Remove-Item -Force "vens\mempalace_adapter\mempalace_minimal_mcp.py"
Remove-Item -Force "vens\onboarding-reports\mempalace_minimal.log"
```

Usage example (point Continue `mcpServers` to the shim):

```yaml
mcpServers:
  - name: MemPalaceMinimal
    command: C:\\Users\\Baxter\\Desktop\\Vens Constitution\\.venv\\Scripts\\python.exe
    args:
      - C:\\Users\\Baxter\\Desktop\\Vens Constitution\\vens\\mempalace_adapter\\mempalace_minimal_mcp.py
    cwd: C:\\Users\\Baxter\\Desktop\\Vens Constitution\\vens\\mempalace_adapter
    connectionTimeout: 10
```

Notes
- This shim is intentionally minimal. It does not implement the full MCP spec — only
  a safe echo/ok response to allow Continue to establish a stdio connection and proceed.
# MemPalace Adapter

Small adapter used by Vens to produce MCP memory markdown files from a profile dictionary.

Usage example:

```py
from vens.mempalace_adapter import save_profile_memory
path = save_profile_memory(profile_dict)
print(path)
```

License: MIT (adapted from upstream MemPalace per project license).
