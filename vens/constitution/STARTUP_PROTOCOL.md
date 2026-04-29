# Vens Startup Protocol v1.0

## Purpose
This protocol defines the standard startup sequence for initializing the Vens multi-agent system for a new project or session.

## Startup Sequence

### Step 1 — Launch
Run `start_vens.bat` from `/vens/orchestrator/`

### Step 2 — VS Code Opens
The script opens VS Code into the Vens workspace automatically.

### Step 3 — Setup Wizard Opens
`SETUP_WIZARD.txt` opens in your editor with fill-in-the-blank fields:
- Project name and source path
- Primary objective and constraints
- First task description and assignment
- Trigger command (START, HALT, etc.)

### Step 4 — User Fills In & Saves
Fill in every `(FILL IN)` placeholder, then save the file (Ctrl+S).

### Step 5 — Apply Setup
Press any key in the terminal. The `apply_setup.js` script reads your answers and distributes them into:
- `PROJECT_SOURCE_PATH.txt`
- `MAIN_GOAL.txt`
- `TRIGGER_WORKFLOW.txt`
- `pending.json`
- `active_agent.txt`

### Step 6 — Orchestrator Starts
The live dashboard launches automatically, watching for agent turn changes.

## Rules
- Only HUMAN may run the startup protocol.
- Agents must never execute `start_vens.bat` or `apply_setup.js`.
- The Setup Wizard must be completed before the system activates.

END OF STARTUP PROTOCOL v1.0
