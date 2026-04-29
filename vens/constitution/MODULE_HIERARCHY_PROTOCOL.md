# Module Hierarchy Protocol v1.0

## 1. Purpose
This protocol defines how modules and blocks function as the canonical operational baseline for all project work. Modules and blocks are the authoritative source of truth for planning, implementation, verification, gating, and progress tracking.

## 2. Hierarchical Structure

### 2.1 Modules (Lettered: A, B, C, D…)
Modules represent foundational stability layers. They define what must exist in the system.  
Module order reflects architectural dependency, not execution sequence.

### 2.2 Blocks (Numbered: 1, 2, 3, 4…)
Blocks represent sequential execution steps within a module.  
Block order reflects logical build sequence, not architectural importance.

### 2.3 Combined Addressing
Every task is uniquely identified as:
Module <Letter> Block <Number>

Example:
Module D Block 5

## 3. Canonical Truth Model

### 3.1 Modules and Blocks Are Authoritative
Agents must treat module/block definitions as the canonical baseline for:
- Planning
- Implementation
- Verification
- Gating conditions
- Progress tracking
- Escalation

### 3.2 Project Summary Is Non‑Authoritative
The project summary is a human convenience layer only.  
It cannot override modules or blocks.

## 4. Gating Conditions

### 4.1 Blocks May Contain Explicit Requirements
Examples:
- Required test counts
- Dependency completions
- Stability prerequisites
- Cross-module readiness

### 4.2 Enforcement
Agents must verify all gating conditions before advancing from Block N to Block N+1.  
If unmet, agents must halt and escalate.

## 5. Agent Responsibilities

### 5.1 ANTIGRAVITY
- Consults module hierarchy before planning
- Verifies block completion
- Enforces gating conditions
- Detects contradictions
- Escalates when necessary

### 5.2 COPILOT
- Implements only the active block
- Never skips ahead
- Never bypasses gating conditions
- Reports deviations or missing information

## 6. Drift Prevention

Agents must:
- Anchor all reasoning to modules/blocks
- Never infer progress
- Never assume readiness
- Never rely on the project summary for correctness

If drift is detected:
ESCALATE: MODULE_DRIFT <description>

## 7. Progress Tracking

Agents must always be able to state:
- Current module
- Current block
- Completion status
- Outstanding gating conditions
- Next required action

Example:
"We are in Module D Block 5.  
20 cargo tests remain before Block 6 can begin."

## 8. Completion Rules

A block is complete only when:
- All requirements are satisfied
- All tests pass
- All dependencies are met
- ANTIGRAVITY verifies stability
- COPILOT confirms implementation
- Stability score ≥ 10/15

END OF MODULE HIERARCHY PROTOCOL v1.0
