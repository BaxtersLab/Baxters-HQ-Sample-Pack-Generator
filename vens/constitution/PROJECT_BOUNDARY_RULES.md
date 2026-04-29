# Project Boundary Rules v1.0

## 1. Purpose
All project build files, application code, and repository assets must remain within the project's designated source directory. This prevents agents from scattering files across the filesystem.

## 2. Source Path Authority
The canonical project source path is defined in:
`/vens/constitution/user/PROJECT_SOURCE_PATH.txt`

Agents must read this file before creating, modifying, or moving any project files.

## 3. Rules

### Agents MUST:
- Keep all source code, build files, configs, and assets inside the designated project folder
- Use the path defined in `PROJECT_SOURCE_PATH.txt` as the project root
- Create subdirectories only within that root
- Treat the project folder name as the canonical project name

### Agents MUST NOT:
- Create project files outside the designated source path
- Place build artifacts, configs, or code in `/vens/` (Vens is governance only)
- Place project files on the Desktop, in temp directories, or in unrelated folders
- Rename or relocate the project root directory

## 4. Separation of Concerns
- `/vens/` = governance, constitution, state, tasks, messages, logs
- `<PROJECT_SOURCE_PATH>` = all code, builds, tests, docs, assets

These two directories must never intermix their contents.

## 5. Escalation
If an agent cannot determine the correct project path:

> Canonical escalation format defined in: VENS_CONSTITUTION.md §6
> Use tag: `PROJECT_PATH_MISSING`

END OF PROJECT BOUNDARY RULES v1.0
