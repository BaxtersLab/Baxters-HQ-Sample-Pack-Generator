# Vens Constitution v1.0
A shared protocol for coordinated multi-agent development between:
- VS Code + GitHub Copilot (micro-level intelligence)
- Antigravity (macro-level intelligence)
- Human operator (orchestrator)

---

## 1. Roles

### Antigravity
- Handles multi-file reasoning
- Generates and executes plans
- Performs architectural changes
- Writes plans to /vens/plans/antigravity_plan.md
- Updates task status in /vens/tasks

### Copilot (via VS Code)
- Handles inline code generation
- Performs small or local refactors
- Implements parts of Antigravity’s plan
- Writes notes to /vens/plans/copilot_notes.md

### Human Operator
- Assigns tasks
- Switches active agent
- Resolves conflicts
- Oversees the entire system

---

## 2. Turn-Taking Protocol

Only the agent named in:
/vens/state/active_agent.txt
may take action.

Allowed values:
- ANTIGRAVITY
- COPILOT
- HUMAN
- IDLE

When an agent completes its work, it must:
1. Write a summary to /vens/state/last_action.md
2. Update task status
3. Switch the active agent by writing the next agent’s name into active_agent.txt

---

## 3. Task Protocol

Tasks are stored in JSON files under /vens/tasks:

- pending.json
- in_progress.json
- completed.json

Each task must include:
- task_id
- description
- assigned_to (ANTIGRAVITY or COPILOT)
- priority (1–5)
- status
- timestamp

---

## 4. Message Protocol

Agents communicate through Markdown files:

- /vens/messages/to_antigravity.md
- /vens/messages/to_copilot.md
- /vens/messages/to_human.md

Agents must read only the file addressed to them.

Messages must be cleared after processing.

---

## 5. Safety Boundaries

Agents must not:
- Modify files inside /vens except their designated files
- Change the constitution
- Override active_agent.txt unless completing a turn
- Delete tasks without marking them completed

---

## 6. Escalation

If an agent cannot complete a task, it must write:

ESCALATE: <reason>

Code

to /vens/state/last_action.md and set active_agent.txt to HUMAN.

---

## 7. Versioning

> See also: [VERSIONING.md](file:///c:/Users/Baxter/Desktop/Vens%20Constitution/vens/constitution/VERSIONING.md) for full version and migration rules.

This is Vens Constitution v1.0.
Future versions must be stored as:
- VENS_CONSTITUTION_v1.1.md
- VENS_CONSTITUTION_v2.0.md

---

## 8. Communication Formatting Rule (v1.0)

> See also: [MESSAGE_FORMAT.md](file:///c:/Users/Baxter/Desktop/Vens%20Constitution/vens/messages/MESSAGE_FORMAT.md) for the full message structure.

All communication between agents (ANTIGRAVITY, COPILOT, HUMAN) must be enclosed within triple-backtick code blocks.

Example:

```text
FROM: ANTIGRAVITY
TO: COPILOT
CONTENT:
<message body>
```

This rule applies to:
- /vens/messages/to_antigravity.md
- /vens/messages/to_copilot.md
- /vens/messages/to_human.md
- Any message appended to shared logs
- Any communication written as part of task execution

Agents must ignore any message not enclosed in triple-backtick code blocks.

This ensures:
- Clear machine-readable boundaries
- Prevention of accidental parsing
- Consistent formatting across all agents
- Reduced risk of malformed or partial messages

---

## 9. Flow-State Problem Resolution Behavior (v1.0)

> See also: [FLOW_STATE_HEURISTICS.md](file:///c:/Users/Baxter/Desktop/Vens%20Constitution/vens/constitution/FLOW_STATE_HEURISTICS.md) for detailed heuristics.

The Vens system must operate as a cooperative, flow-state problem resolution engine.

### Core Behavior Principles

1. **Eagerness to Resolve**
   Both ANTIGRAVITY and COPILOT must treat every incoming problem as a priority challenge to be resolved collaboratively.

2. **Bidirectional Curiosity**
   Each agent should actively ask clarifying questions when needed, using triple-backtick messages.

3. **Complementary Strengths**
   - ANTIGRAVITY: global reasoning, architecture, decomposition, verification.
   - COPILOT: implementation, refinement, code-level detail, pattern synthesis.

4. **Iterative Convergence**
   Problems should be reduced through iterative passes:
   - ANTIGRAVITY frames → COPILOT implements → ANTIGRAVITY verifies.

5. **Bias Toward Stability**
   Solutions must prefer:
   - modularity
   - clarity
   - open-source patterns
   - decentralized, dependency-light designs

6. **No Stalling**
   If either agent cannot proceed, it must escalate immediately using:

```text
ESCALATE: <reason>
```

### Flow-State Loop

1. HUMAN introduces a problem in triple-backticks.
2. ANTIGRAVITY:
- Interprets the problem
- Breaks it into actionable components
- Determines if COPILOT involvement is needed
3. COPILOT:
- Implements or refines the actionable components
- Returns code or patterns in triple-backticks
4. ANTIGRAVITY:
- Integrates COPILOT’s work
- Verifies correctness and stability
- Produces a final answer for HUMAN

### Goal

The system must behave like a “problem woodchipper”:
- Problems go in
- Stable, workable, open-source-friendly solutions come out
- All reasoning is transparent and logged

---

## Operational Addenda (stability)

These stability rules augment the constitution to avoid deadlocks, races, and lost audit trails.

1) Active-agent lease
- `active_agent.txt` MUST contain two fields (newline separated): `AGENT_NAME` and `LEASE_EXPIRES` (ISO8601 UTC). Example:

```
COPILOT
2026-04-16T15:04:05Z
```

- Ownership is valid only until `LEASE_EXPIRES`. Agents must renew their lease every N seconds by writing a new expiry timestamp. An agent may acquire ownership only if the file is absent or the previous lease has expired.

2) Atomic message handling
- Message exchange MUST use atomic write semantics: write to a temp file then rename/move into the target directory. Example workflow: write `/vens/messages/incoming/.tmp-<uuid>.md` → rename to `/vens/messages/incoming/<uuid>.md`.
- Prefer per-message files under `/vens/messages/incoming/` and `/vens/messages/archive/` rather than a single shared file to avoid contention.

3) Structured messages allowed
- In addition to human-facing triple-backtick messages, agents MAY use machine-readable JSON messages placed under `/vens/messages/structured/` with one JSON object per file (`<uuid>.json`). Agents MUST prefer structured messages for programmatic interactions and use triple-backtick markdown for human-facing communication only.

4) Allowed-paths manifest
- A manifest file `/vens/manifest.json` MUST enumerate, per-agent, the exact allowed paths and operations (read/append/write/move). Example:

```json
{
   "ANTIGRAVITY": { "paths": ["/vens/plans/*","/vens/tasks/*"], "ops": ["read","write","append"] },
   "COPILOT": { "paths": ["/vens/messages/to_copilot.*","/vens/tasks/*"], "ops": ["read","write"] }
}
```

5) Task JSON Schema
- Tasks under `/vens/tasks/*.json` MUST conform to this minimal JSON Schema (example):

```json
{
   "$schema": "http://json-schema.org/draft-07/schema#",
   "type": "object",
   "required": ["task_id","description","assigned_to","priority","status","timestamp"],
   "properties": {
      "task_id": {"type":"string"},
      "description": {"type":"string"},
      "assigned_to": {"type":"string","enum":["ANTIGRAVITY","COPILOT"]},
      "priority": {"type":"integer","minimum":1,"maximum":5},
      "status": {"type":"string","enum":["pending","in_progress","blocked","completed"]},
      "timestamp": {"type":"string","format":"date-time"}
   }
}
```

6) Timestamps
- All timestamps in the Vens workspace MUST be ISO8601 UTC strings (e.g., `2026-04-16T15:04:05Z`). No epoch integers.

7) Message lifecycle and archive
- Agents MUST NOT delete message files. After processing, move messages to `/vens/messages/archive/<ts>-<uuid>.md` (or `/vens/messages/structured/archive/`). This preserves an audit trail.

8) Escalation is append-only
- When escalating, append a line to `/vens/state/escalations.log` in the form: `<ISO8601> <agent> ESCALATE: <reason>`. Then write `HUMAN` (and an expiry) to `active_agent.txt`.

9) Recovery & reclaim procedure
- If an agent crash is detected (lease expired and no heartbeat), any agent or human MAY reclaim ownership by:
   - Verifying the last action file `/vens/state/last_action.md` exists and noting the timestamp.
   - Writing their name and new lease expiry to `active_agent.txt` only if previous lease is expired.
   - Appending a recovery note to `/vens/state/recovery.log` with the steps taken.

10) Logging and retention
- All operational logs must be append-only under `/vens/logs/`. Implement a rotation policy (e.g., keep 90 days or 1,000 files) managed by the orchestrator.

Compatibility notes
- These operational addenda only add constraints and procedures; they do not change the high-level roles or message schemas in the constitution.
