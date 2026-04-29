# Vens Planning Cycle v1.0

1. HUMAN assigns a task in /vens/tasks/pending.json
2. HUMAN sets active_agent.txt = ANTIGRAVITY
3. ANTIGRAVITY:
   - Reads the task
   - Generates a plan
   - Writes plan to /vens/plans/antigravity_plan.md
   - Moves task to in_progress.json
   - Sets active_agent.txt = COPILOT
4. COPILOT:
   - Reads the plan
   - Implements code-level changes
   - Writes notes to /vens/plans/copilot_notes.md
   - Sets active_agent.txt = ANTIGRAVITY
5. ANTIGRAVITY:
   - Verifies implementation
   - Updates task status
   - Sets active_agent.txt = HUMAN
