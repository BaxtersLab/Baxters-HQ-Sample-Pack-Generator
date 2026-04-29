# Vens Cycle Test v1.0

Purpose: Validate the full Vens workflow.

Test Steps:
1. HUMAN creates a simple task in pending.json
2. HUMAN sets active_agent.txt = ANTIGRAVITY
3. ANTIGRAVITY generates a plan
4. ANTIGRAVITY hands off to COPILOT
5. COPILOT implements code changes
6. COPILOT hands off to ANTIGRAVITY
7. ANTIGRAVITY verifies changes
8. ANTIGRAVITY completes the task
9. HUMAN reviews logs and memory index

Expected Result:
- No conflicts
- No rule violations
- All logs populated
- Task marked COMPLETED
