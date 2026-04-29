# Vens Rollback Protocol v1.0

Rollback is triggered when:
- Verification fails
- A task is corrupted
- Unexpected file changes occur
- A conflict escalates

Rollback steps:
1. ANTIGRAVITY creates a snapshot of affected files in /vens/rollback/<task_id>/
2. ANTIGRAVITY restores the last known good version
3. ANTIGRAVITY writes a rollback report to /vens/state/last_action.md
4. ANTIGRAVITY sets active_agent.txt = HUMAN

Snapshots must include:
- Modified files
- The plan that caused the change
- The verification failure reason
