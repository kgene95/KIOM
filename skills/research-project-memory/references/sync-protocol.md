# Synchronization protocol

Use this protocol when resuming, updating, or handing off research work across GitHub, the UST shared OneDrive workspace, local terminal folders, Codex, Work, another GPT account, or another AI system.

## Canonical analysis layout

Keep each analysis in one canonical folder. Prefer this layout when creating or normalizing a project:

```text
<analysis>/
├── 00_PROJECT/
│   ├── README_AGENT.md
│   ├── CURRENT_STATUS.md
│   ├── CHANGELOG.md
│   ├── file_inventory.csv
│   ├── manifest.json
│   └── checkpoint.md
├── scripts/
├── raw/
├── results/
└── figures/
```

Existing workflow-specific names such as `NP_manifest.json`, `docking_manifest.json`, `network_pharmacology_checkpoint.md`, or `docking_checkpoint.md` remain valid. Do not rename or duplicate them merely to fit the generic layout; record migrations explicitly.

## Resume protocol

1. Resolve the canonical project and analysis folder.
2. Read `00_PROJECT/README_AGENT.md` when present, then `CURRENT_STATUS.md` / `PROJECT_STATE.md`, then the relevant checkpoint.
3. Inspect manifests and `file_inventory.csv` only as needed for the current task.
4. Reuse completed outputs. Do not rerun completed analyses unless the user requests it or the checkpoint identifies invalidation, changed inputs, changed methods, or failed QC.
5. Load the smallest context sufficient for the next action.

## Update and synchronization protocol

After meaningful work:

1. Update the relevant current-state file, checkpoint, manifest, decision log, and inventory only when those records changed.
2. Append a concise `CHANGELOG.md` entry with date, files changed, reason, and validation state.
3. Synchronize changed final outputs, scripts, figures, and project records by default. Exclude temporary files and bulky raw inputs unless explicitly needed.
4. Compare remote state before replacing a file. Never overwrite a newer remote file silently.
5. Write compact versioned state to GitHub when available.
6. Send large binary/raw artifacts to the canonical UST shared workspace only after the destination passes the access gate in `workspace-locations.md`.
7. Report synchronized files, skipped files, conflicts, and failed destinations separately.

## State-file invariants

- Never create duplicate authoritative `CURRENT_STATUS.md`, `PROJECT_STATE.md`, `CHANGELOG.md`, manifest, checkpoint, or inventory files for the same analysis without a documented migration.
- Never let memory records overwrite scientific raw data or validated workflow outputs.
- Preserve existing scientific conclusions and provenance; change them only when new evidence supports the change.
- A successful local analysis remains valid even when a remote synchronization step fails.
- Treat GitHub state and OneDrive binary storage as complementary, not interchangeable.

## Naming and folder-creation rules

Keep these concepts distinct: project, workflow/analysis, material/extract, compound, target/receptor, experiment group, and output type.

Before creating a folder:

1. identify its parent project and semantic level;
2. verify the project-to-folder mapping in `workspace-locations.md`;
3. check for an existing same-name folder;
4. do not infer a new project/material from a similar name;
5. preserve user spelling, punctuation, stereochemical marks, and capitalization;
6. record newly created project/analysis folders in the relevant project index or changelog.

If filename and project mapping disagree, stop and resolve the project identity before upload or move.

## Conflict policy

When local, GitHub, and UST shared-workspace copies disagree:

1. do not silently overwrite;
2. compare timestamps, manifests/checkpoints, file hashes when available, and changelog entries;
3. prefer the newest authoritative validated state, not simply the newest file timestamp;
4. preserve both copies when scientific provenance is uncertain;
5. record the conflict and resolution.

## Cross-account handoff

For another GPT account or AI system, prefer a small handoff bundle containing `AI_CONTEXT.md`, project state, decisions, relevant manifest/checkpoint, and exact file locations. Do not require the receiving system to crawl the full repository or large OneDrive tree.
