# Project identity and continuation records

Use this procedure before reading, creating, uploading, moving, or updating a docking file in a shared workspace.

## Identity preflight

1. Read the workspace `PROJECT_INDEX.md` and the nearest project status/readme file.
2. Resolve four names separately and record all four before any write:
   - material identity (for example, `CMPE` / 참외껍질),
   - project root (for example, `01_CMPE`),
   - analysis package (for example, `CMPE_Docking`),
   - analysis branch (for example, `CMPE_Docking_Revalidation`).
3. Treat storage-category names such as `02_MGC/MGC_Docking` as different projects unless the index explicitly maps them to the current material.
4. Reuse an existing exact-match directory. Never create a second project folder because a path was guessed from a storage category.

## Required continuation records

Every project or analysis package must keep these records current:

- `PROJECT_README.md` or `00_PROJECT/README_AGENT.md`: identity, purpose, canonical path, scope, and “do not rerun” rule.
- `CURRENT_STATUS.md`: completed, limited, blocked, and next actions.
- `CHANGELOG.md`: dated reason for every calculation, upload, move, or record update.
- `file_inventory.csv`: relative path, file role, size, modified time, SHA-256, and sync destination.
- `GITHUB_ONEDRIVE_HANDOFF.md`: storage roles, last Git commit, last OneDrive sync, conflicts, and resume instructions.
- `FOLDER_STATUS.md` in each analysis branch and each newly created project-level folder: scope, status, and immediate contents.

The first page of every continuation record must state the material and project names explicitly. A new agent must read these records before opening raw structures or rerunning calculations.

## Folder creation and update rule

Folder creation is a recorded event. The same operation that creates a new project-level or analysis-branch folder must generate its `FOLDER_STATUS.md`, add the folder to `PROJECT_INDEX.md` or the nearest project map, and append a dated `CHANGELOG.md` entry. File uploads and updates must append their destination, source, reason, and verification result to the handoff/changelog records.

Use a deterministic record generator such as `scripts/update_project_records.py`; it must fail if the expected material/project identity does not match the existing index. Never silently rename, move, overwrite, or merge projects.

## Continuation behavior

When the records are present and current, resume from the documented checkpoint and hashes. Do not recompute a completed docking branch merely because the work is opened from another account, another AI, or another OneDrive/GitHub clone. Reopen raw data only for a documented unresolved item.
