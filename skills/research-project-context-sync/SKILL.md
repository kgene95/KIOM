---
name: research-project-context-sync
description: Resume and synchronize research-analysis folders across Codex, GitHub, and OneDrive using existing project state files and minimal re-reading.
metadata:
  short-description: Sync research analysis context and outputs
---

# Research project context sync

Use this skill when resuming, updating, or handing off a research analysis stored in GitHub and OneDrive.

## OneDrive workspace discovery

Treat the user's OneDrive workspace root as the stable entry point. Projects are subfolders beneath that root; do not hard-code one project's share URL into the skill. Read the workspace-level `PROJECT_INDEX.md` first when present, then select the requested project folder and its analysis-specific `00_PROJECT/` records. If the index is missing, inspect immediate child folders and create or update the index only when the user authorizes project organization.

## Storage locations for this workspace

- OneDrive account: `chskim@office.ust.ac.kr`
- OneDrive workspace root: `LG_노트북/`
- Local OneDrive mirror: `C:\Users\LG\OneDrive - UST\LG_노트북\`
- GitHub repository: `https://github.com/kgene95/KIOM`
- GitHub project root: `01_CMPE/` (CMPE), with each analysis in its own subfolder

Use the OneDrive workspace root for shared files and the GitHub repository for versioned records. Keep project-relative paths identical wherever possible.

## Canonical analysis layout

Each analysis has one canonical folder. Its project records live in `00_PROJECT/`:

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

Existing analysis-specific names such as `docking_manifest.json` and `docking_checkpoint.md` remain valid during migration. Do not duplicate or rename them without recording the change.

## Resume protocol

1. Identify the canonical analysis folder from the repository structure.
2. Read `00_PROJECT/README_AGENT.md`, then `CURRENT_STATUS.md` and `checkpoint.md` (or the analysis-specific checkpoint name).
3. Inspect `manifest.json` and `file_inventory.csv` only as needed to answer the current request.
4. Reuse completed outputs; do not rerun completed analyses unless the user requests a rerun or the checkpoint identifies invalid results.
5. Treat OneDrive as the shared file workspace and GitHub as the versioned project record. Keep their relative paths identical.

## Update and synchronization protocol

After producing or revising analysis outputs:

1. Update the relevant `CURRENT_STATUS.md`, checkpoint, manifest, and inventory.
2. Append a concise entry to `CHANGELOG.md` with date, files changed, reason, and validation state.
3. Synchronize only changed final outputs, scripts, figures, and project records by default. Exclude temporary files and large raw inputs unless explicitly requested.
4. Compare remote files before replacing them. Do not overwrite a newer remote file or delete files automatically; record conflicts for review.
5. Commit and push the GitHub changes with a descriptive message when authentication is available.
6. Upload or update the same relative paths in OneDrive when access is available.
7. Report synchronized files, skipped files, conflicts, and any failed destination separately.

## State-file invariants

- Never create a second `CURRENT_STATUS.md`, `CHANGELOG.md`, `manifest.json`, or inventory for the same analysis.
- Never let the skill's own records replace analysis records.
- Preserve existing scientific conclusions and provenance; update them only when new evidence supports the change.
- A successful local analysis remains valid even if a remote synchronization fails.

## Naming and folder-creation rules

- Keep these concepts distinct: project name, analysis/workflow name, material or compound name, target/receptor name, experiment group, and output type.
- Before creating a folder, identify its parent project and its exact semantic level. Do not place an existing material name inside a newly requested material folder unless the user explicitly specifies that hierarchy.
- Do not infer a new material, compound, or project name from a similar existing folder. Ask when the requested name or parent is ambiguous.
- Preserve the user's spelling, punctuation, stereochemical marks, and capitalization for material names; use a separate stable machine identifier only when needed.
- Check for an existing same-name folder at the intended level before creating one. If found, update it only when the user clearly requested an update; otherwise report the collision.
- Record newly created project, analysis, or material folders in the appropriate `PROJECT_INDEX.md`, `README_AGENT.md`, or `CHANGELOG.md`.
