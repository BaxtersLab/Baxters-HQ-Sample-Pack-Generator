# Vens Conflict Resolution v1.0

Conflicts occur when:
- Agents disagree on implementation
- A task cannot be completed
- Unexpected file changes appear
- Plans contradict each other

Resolution steps:
1. The detecting agent writes a message to /vens/messages/to_human.md
2. The agent writes ESCALATE: <reason> to last_action.md
3. The agent sets active_agent.txt = HUMAN
4. HUMAN resolves the conflict manually
5. HUMAN updates the task and reassigns it
