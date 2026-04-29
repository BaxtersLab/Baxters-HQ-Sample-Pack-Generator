# Recovery Protocol v1.0

## 1. Purpose
This protocol defines how Vens agents recover from drift, instability, contradictions, or systemic failures.

## 2. Recovery Triggers
Recovery is triggered when:

- Drift is detected  
- Stability score < 10/15  
- Gating conditions fail  
- Module/block contradictions appear  
- Execution cycles stall  
- Agents disagree on next action  

## 3. Recovery Steps

### Step 1 — Halt
Stop all forward progress immediately.

### Step 2 — Identify
Determine:
- Drift type  
- Drift source  
- Drift impact  
- Affected modules/blocks  

### Step 3 — Re‑Anchor
Re‑align to:
- Module Hierarchy Protocol  
- Stability Scoring System  
- Active module/block state  
- Gating conditions  

### Step 4 — Recompute
Recompute:
- Stability score  
- Dependencies  
- Preconditions  
- Next valid action  

### Step 5 — Resume
Resume execution only when:
- Stability score ≥ 10/15  
- No contradictions remain  
- All gating conditions are satisfied  

## 4. Escalation
If recovery fails:

> Canonical escalation format defined in: VENS_CONSTITUTION.md §6
> Use tag: `RECOVERY_FAILURE`

## 5. Logging
All recovery events must be appended to the Long‑Cycle Memory Ledger.

END OF RECOVERY PROTOCOL v1.0
