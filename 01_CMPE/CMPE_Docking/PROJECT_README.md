# CMPE Docking project

## Identity lock

- Material: **CMPE (참외껍질)**
- Workspace: `LG_노트북`
- Project root: `01_CMPE`
- Analysis package: `01_CMPE/CMPE_Docking`
- Active revalidation branch: `01_CMPE/CMPE_Docking/CMPE_Docking_Revalidation`
- Separate project: `02_MGC/MGC_Docking` (do not place CMPE files there)

## Purpose

This package stores the reproducibility revalidation of manuscript Fig. 3(B). The primary interpretation is vitexin-4″-O-glucoside docked to human IKKβ `4KIK` chain B. Naringenin is a comparator. COX-2 `5IKR` remains a separate blocked branch because the deposited COH cobalt metalloporphyrin requires a reviewed Vina-compatible treatment.

The package is a continuation record, not a request to rerun docking. A new account or AI must read this file, `00_PROJECT/FOLDER_STATUS.md`, `00_PROJECT/CURRENT_STATUS.md`, the manifest, and the checkpoint before opening raw structures.

## Required update rule

Before every upload, update, move, or folder creation:

1. Reconfirm the four names above against `LG_노트북/PROJECT_INDEX.md`.
2. Reuse the exact existing folder; do not infer a project from `MGC_Docking` or create a duplicate.
3. Generate or update `FOLDER_STATUS.md`, `CURRENT_STATUS.md`, `CHANGELOG.md`, and `file_inventory.csv`.
4. Record source, destination, reason, timestamp, and verification result in `GITHUB_ONEDRIVE_HANDOFF.md`.
5. Do not rerun completed calculations when hashes and checkpoints already document them.

## Storage roles

- OneDrive: raw structures, PDB/PDBQT/SDF, logs, poses, PDFs, figures, and complete review materials.
- GitHub: skill files, scripts, manifests, checkpoints, Markdown, and small reproducibility tables.
- ZIP archives are historical snapshots only; do not create new skill or recovery ZIPs.
