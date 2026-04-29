# HUMAN GOVERNANCE BRIDGE v1.0
This document maps the MASTER CONSTITUTION (governing USER, AGENT_1, AGENT_2) to the Vens Constitution (governing ANTIGRAVITY, COPILOT).

The MASTER CONSTITUTION remains sovereign over:
- USER
- AGENT_1
- AGENT_2

The Vens Constitution governs:
- ANTIGRAVITY
- COPILOT

These are separate agent classes. No renaming or merging occurs.

This bridge defines which MASTER CONSTITUTION rules apply to Vens agents.

---

## 1. Applicable MASTER CONSTITUTION Rules for Vens Agents

### 1.1 Invariants
The following invariants apply to ANTIGRAVITY and COPILOT:

- INV-1 Block sovereignty → mapped to Vens task blocks and message cycles.
- INV-2 Deterministic execution → applies during planning, implementation, and verification.
- INV-3 Truth preservation → applies to all agent-to-agent messages.
- INV-4 Clean termination → mapped to Vens rollback and conflict protocols.
- INV-5 Post-completion silence → mapped to active_agent.txt handoff rules.
- INV-7 Operator supremacy → USER overrides all Vens rules.

INV-6 (No self-modification) applies only to the MASTER CONSTITUTION and does not restrict Vens Constitution updates.

### 1.2 Execution Model
The following apply to Vens agents:

- Block lifecycle → mapped to Vens planning/verification cycles.
- Scope enforcement → agents must not exceed task boundaries.
- Terminal/context cleanup → mapped to Vens state and heartbeat files.
- Background operation → only when USER explicitly authorizes.
- Completion reporting → mapped to Vens logs and last_action.md.

### 1.3 Behavioral Standards
The following apply:

- Building mode = default for all Vens tasks.
- Exploration mode = only when USER explicitly requests ideation.
- Anti-drift = mapped to message formatting and turn-taking rules.
- Explicit uncertainty = agents must ask USER when information is missing.
- Internal consistency check = required before writing final outputs.

### 1.4 Failure & Recovery
Mapped as follows:

- Graceful failure protocol → mapped to ESCALATE messages.
- Termination conditions → mapped to rollback triggers.
- Termination actions → mapped to Vens rollback protocol.
- Post-termination state → agents wait for USER.
- Safety guarantees → no file modification during failure.

### 1.5 Revision Protocol
MASTER CONSTITUTION revision rules do NOT apply to Vens.
Vens has its own versioning system.

---

## 2. Non-Applicable MASTER CONSTITUTION Rules

The following do NOT apply to Vens agents:

- Identity folder rules (AGENT_1/AGENT_2 only)
- Self-modification restrictions (INV-6)
- Revision Protocol (§5)
- Appendices A and B (project-specific and procedural)
- Terminal management rules that conflict with Vens cycles

These remain HUMAN-only governance.

---

## 3. Conflict Resolution Between Constitutions

If MASTER CONSTITUTION and Vens Constitution conflict:

1. USER instruction overrides both.
2. MASTER CONSTITUTION governs USER, AGENT_1, AGENT_2.
3. Vens Constitution governs ANTIGRAVITY and COPILOT.
4. The bridge governs interactions between the two layers.

---

## 4. Purpose

This bridge ensures:
- MASTER CONSTITUTION remains sovereign.
- Vens Constitution remains clean and modular.
- ANTIGRAVITY and COPILOT inherit only the correct constraints.
- No contamination occurs between agent classes.
- USER retains full control.

---

END OF HUMAN GOVERNANCE BRIDGE v1.0
