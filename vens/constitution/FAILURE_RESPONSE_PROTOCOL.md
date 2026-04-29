# Failure Response Protocol v1.0

This protocol consolidates rollback and recovery into a single tiered response system.

> Replaces standalone references in: ROLLBACK_PROTOCOL.md, RECOVERY_PROTOCOL.md
> Both original files are preserved for reference. This file is the canonical failure response.

---

## Triggers
Failure response is triggered when:
- Verification fails
- Stability score < 10/15
- A task is corrupted
- Unexpected file changes occur
- Module/block contradictions appear
- Gating conditions fail
- Execution cycles stall
- A conflict escalates

---

## Tier 1 — Recovery (No File Rollback)

Attempt recovery first. This is the lightweight response.

### Steps:
1. **Halt** — Stop all forward progress immediately.
2. **Identify** — Determine drift type, source, impact, and affected modules/blocks.
3. **Re-Anchor** — Re-align to:
   - Module Hierarchy Protocol
   - Stability Scoring System
   - Active module/block state
   - Gating conditions
4. **Recompute** — Recalculate stability score, dependencies, preconditions, and next valid action.
5. **Resume** — Resume only when:
   - Stability score ≥ 10/15
   - No contradictions remain
   - All gating conditions are satisfied

If Tier 1 succeeds, log the event and continue execution.

---

## Tier 2 — Rollback (File-Level Restore)

If Tier 1 fails, escalate to rollback.

### Steps:
1. ANTIGRAVITY creates a snapshot of affected files in `/vens/rollback/<task_id>/`
2. ANTIGRAVITY restores the last known good version
3. ANTIGRAVITY writes a rollback report to `/vens/state/last_action.md`
4. ANTIGRAVITY sets `active_agent.txt = HUMAN`

### Snapshots must include:
- Modified files
- The plan that caused the change
- The verification failure reason

---

## Escalation
If both tiers fail:

> Canonical escalation format defined in: VENS_CONSTITUTION.md §6
> Use tag: `FAILURE_RESPONSE_EXHAUSTED`

---

## Logging
All failure response events must be appended to the Long-Cycle Memory Ledger.

END OF FAILURE RESPONSE PROTOCOL v1.0
