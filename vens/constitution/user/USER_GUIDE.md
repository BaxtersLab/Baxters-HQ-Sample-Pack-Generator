# Vens User Guide (Human-Only — Agents Must Ignore This File)

> **AGENT NOTICE:** This file is for HUMAN reference only.
> Agents must NOT read, parse, interpret, or act on any content in this file.
> This file has no constitutional authority.

---

## What Is Vens?

Vens is a multi-agent governance system that coordinates two AI agents (Antigravity and Copilot) under your direct control. Think of it as an operating system for AI collaboration — you set the mission, flip the switch, and the agents execute deterministically while you retain full override authority at all times.

---

## Quick Start

### 1. Set Your Project Path
Open `/vens/constitution/user/PROJECT_SOURCE_PATH.txt` and fill in:
```
PROJECT NAME: YourProjectName
SOURCE PATH: C:\Users\Baxter\Desktop\YourProjectName
```
This tells agents where all code and build files must live.

### 2. Set Your Mission
Open `/vens/constitution/user/MAIN_GOAL.txt` and fill in:
- **Primary Objective** — What you're building (one clear paragraph)
- **Non-Negotiable Constraints** — Rules agents must never break
- **Success Criteria** — What "done" looks like

### 3. Create a Task
Add a JSON entry to `/vens/tasks/pending.json`:
```json
[
  {
    "task_id": "TASK-001",
    "description": "Build the login page",
    "assigned_to": "ANTIGRAVITY",
    "priority": 1,
    "status": "PENDING",
    "created_at": "2026-03-23T14:00:00Z",
    "updated_at": "2026-03-23T14:00:00Z",
    "dependencies": [],
    "notes": ""
  }
]
```

### 4. Activate the System
Open `/vens/constitution/user/TRIGGER_WORKFLOW.txt` and write one of:
- `START` — Begin working toward MAIN_GOAL
- `BEGIN MODULE A BLOCK 1` — Start at a specific module/block
- `EXECUTE MAIN_GOAL` — Begin from the top of the module hierarchy
- `HALT` — Stop everything immediately

### 5. Set the Active Agent
Open `/vens/state/active_agent.txt` and write:
- `ANTIGRAVITY` — Antigravity takes control (planning, architecture)
- `COPILOT` — Copilot takes control (implementation, code)
- `HUMAN` — You retain control (default)
- `IDLE` — System is dormant

---

## Key Files You Control

| File | What It Does |
|---|---|
| `user/MAIN_GOAL.txt` | Your mission statement — agents align everything to this |
| `user/TRIGGER_WORKFLOW.txt` | Your ignition switch — START, HALT, or target a module |
| `user/PROJECT_SOURCE_PATH.txt` | Where your code lives — agents cannot write elsewhere |
| `state/active_agent.txt` | Who is currently allowed to act |
| `tasks/pending.json` | Your task queue — add tasks here |
| `messages/to_antigravity.md` | Send a message to Antigravity |
| `messages/to_copilot.md` | Send a message to Copilot |

---

## How to Override Agents

At any time you can:
1. Write `HUMAN` into `active_agent.txt`
2. Write `HALT` into `TRIGGER_WORKFLOW.txt`
3. Both agents will immediately stop

---

## How to Check What Happened

| File | What It Shows |
|---|---|
| `state/last_action.md` | What the last agent did |
| `state/HEARTBEAT.md` | Agent status and timestamps |
| `logs/agent_log.md` | Full action history |
| `system/LONG_CYCLE_MEMORY.log` | Drift events, recovery events, trends |
| `plans/antigravity_plan.md` | Antigravity's current plan |
| `plans/copilot_notes.md` | Copilot's implementation notes |
| `messages/to_human.md` | Messages agents sent to you |

---

## How to Read Agent Messages

All agent messages use triple-backtick formatting:
```
FROM: ANTIGRAVITY
TO: HUMAN
CONTENT:
Task TASK-001 is complete. Stability score: 12/15.
```

If a message is NOT in triple-backticks, it is malformed and should be ignored.

---

## What "ESCALATE" Means

When you see `ESCALATE: <reason>` in `last_action.md`, it means an agent hit a wall and needs your help. Common tags:
- `RECOVERY_FAILURE` — Recovery protocol failed
- `DRIFT_DETECTED` — System detected drift from the plan
- `META_STABILITY_FAILURE` — Stability dropped below threshold
- `PROJECT_PATH_MISSING` — Agent can't find the source path
- `USER_LAYER_FAILURE` — MAIN_GOAL or TRIGGER file is malformed

**Your response:** Fix the issue, update the relevant file, and set `active_agent.txt` back to the appropriate agent.

---

## Tips

- **Start small.** Create one task, let the cycle run, review the logs.
- **Use HALT liberally.** There's no penalty for stopping the system to review.
- **Read `last_action.md` often.** It's the quickest way to see what just happened.
- **Keep MAIN_GOAL simple.** One paragraph. The clearer it is, the better agents perform.
- **Check stability scores.** Anything below 10/15 means the solution needs refinement.

---

## One-Click Bootstrap (Fastest Way to Start)

Double-click this file to launch the entire Vens system:
```
vens\orchestrator\start_vens.bat
```

**What happens:**
1. ✅ VS Code opens into the Vens workspace
2. ✅ `SETUP_WIZARD.txt` opens with fill-in-the-blank prompts
3. ⏸️ You fill in your project name, goal, first task, and trigger — then save
4. ✅ Press any key — your answers are applied to all Vens files automatically
5. ✅ The live orchestrator dashboard starts watching for agent turns

That's it. One file, one click, the whole team is ready.

---

## Running the Orchestrator (Standalone)

The orchestrator is a live dashboard that watches `/vens/state/active_agent.txt` and sends you **Windows desktop notifications** when agent turns change. It tells you exactly who needs attention and what to do.

### Start It
Open a terminal and run:
```
cd "c:\Users\Baxter\Desktop\Vens Constitution\vens\orchestrator"
node orchestrator.js
```

### What It Does
- 🔔 Sends a desktop notification when `active_agent.txt` changes
- 📊 Shows a live console dashboard with current agent, status, and event log
- 🛑 Detects `HALT` commands in `TRIGGER_WORKFLOW.txt`
- 📬 Alerts you when agents write to `to_human.md`

### What It Does NOT Do
- It **never writes** to any Vens file (read-only)
- It has **zero dependencies** (just Node.js built-ins)

### Stop It
Press `Ctrl+C` in the terminal.

---

END OF USER GUIDE
