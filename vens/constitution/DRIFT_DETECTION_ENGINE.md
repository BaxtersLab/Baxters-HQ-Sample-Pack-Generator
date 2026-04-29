# Drift‑Detection Engine v1.0

## 1. Purpose
This engine defines how Vens agents detect drift across behavioral, architectural, execution, and module/block layers.

## 2. Types of Drift

### 2.1 Behavioral Drift
- Agents deviating from heuristics  
- Incorrect mode switching  
- Repeated clarification failures  

### 2.2 Architectural Drift
- Module/block contradictions  
- Missing or outdated gating conditions  
- Unstable decomposition patterns  

### 2.3 Execution Drift
- Repeated failures without progress  
- Circular refinement loops  
- Divergent implementation paths  

### 2.4 Namespace Drift
- Inconsistent agent naming  
- Cross‑layer identity bleed  

## 3. Drift Signals
Drift is detected when any of the following occur:

- Stability score decreases across cycles  
- Agents disagree on next action  
- Gating conditions are bypassed  
- Module/block order is violated  
- Contradictions appear in planning  
- Execution cycles repeat without advancement  

## 4. Drift Detection Algorithm
1. Compare current cycle state to stability anchors  
2. Compute stability deltas  
3. Identify contradictions or regressions  
4. Classify drift type  
5. Trigger recovery protocol  

## 5. Escalation
When drift is detected:

> Canonical escalation format defined in: VENS_CONSTITUTION.md §6
> Use tag: `DRIFT_DETECTED <type>`

## 6. Drift Logging
All drift events must be appended to the Long‑Cycle Memory Ledger.

END OF DRIFT‑DETECTION ENGINE v1.0
