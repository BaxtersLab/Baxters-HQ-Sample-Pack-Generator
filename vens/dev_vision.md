# Vens — Development Vision

Purpose
- Provide a repeatable, safe, and auditable workflow to onboard new GGUF models, apply configurations for the Continue/Chatbox integration, and eventually automate the process so the backend agent is optional.

Top-level Goals
- Allow users to download models and apply configurations with a single GUI-driven workflow.
- Validate model availability and responsiveness programmatically (health + minimal chat tests).
- Keep an audit trail and backups so configuration changes are reversible.
- After empirical validation (see success criteria), implement a mechanical patch that can apply profiles and verify the server without invoking the backend agent.

Success Criteria (for automation)
- 5 successful new-model onboarding runs (download → apply → server passes health/test).
- 5 successful existing-configuration activations (select profile → apply → server passes health/test).
- Each success must include logs and a created backup of the previous `config.yaml`.

High-level Roadmap
1. User-facing tooling
   - Deliver the Python `vens/configurator` GUI to list profiles, apply a profile, and run model tests.
   - Provide an accessible launcher (`vens\server-config.bat`).
2. Profile & config management
   - Store named profiles inside `C:\Users\Baxter\.continue\config.yaml` under `profiles`.
   - Provide atomic apply operation that writes selected profile to `models[0]` and sets `active_profile` (existing helper `tools/switch_continue_profile.py`).
3. Testing & validation
   - Implement `Test` that queries `/v1/models` and posts a minimal `/v1/chat/completions` payload; capture response and latency.
4. Logging & backups
   - On each apply, create a timestamped backup in `.continue/backups/` and log operation result.
5. Empirical runs
   - Perform repeated manual runs (as above) until we reach the success criteria.
6. Mechanical patch
   - When criteria met, implement an automated script that: backs up `config.yaml`, applies chosen profile, signals server to reload (Tauri or orchestrator), verifies via test, and rolls back on failure.

Risks & Mitigations
- Risk: server may take time to load large models → add retries/backoff and a configurable timeout.
- Risk: URL or file paths may be incorrect → reject non-direct links and validate Content-Type before writing final file.
- Risk: permission/user mismatch → run all modifications with the same user account and create backups.

Next Milestone (short-term)
- Complete 5 manual onboarding runs and 5 existing-profile activations while logging steps and outcomes. After that, proceed to implement the mechanical patch.
