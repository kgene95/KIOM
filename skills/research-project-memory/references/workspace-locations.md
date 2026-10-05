# Canonical workspace locations

Use these locations as the user's canonical cross-account research workspace unless the user explicitly changes them.

## GitHub

- Canonical repository: `kgene95/KIOM`
- Canonical URL: `https://github.com/kgene95/KIOM`
- Default branch: `main`
- Role: versioned source of truth for project state, decisions, manifests/checkpoints, compact handoff context, scripts, and small reproducibility-critical outputs.
- Known top-level project mappings:
  - `01_CMPE/` = CMPE only
  - `02_MGC/` = MGC only
  - `skills/` = reusable research skills
- Never place a project under another project's canonical folder.

## OneDrive / SharePoint shared workspace

- Canonical owner identity: `chskim@office.ust.ac.kr`
- Canonical shared-folder URL: `https://o365ust-my.sharepoint.com/:f:/g/personal/chskim_office_ust_ac_kr/IgBVWdt-alSnSJwTACfivQyMAY-UWjaYqOdCoDwDMUASmjU?e=fpGsdu`
- Canonical workspace root: `LG_노트북/`
- Known local Windows mirror: `C:\Users\LG\OneDrive - UST\LG_노트북\`
- Access model: direct UST OneDrive connector access may be unavailable. Use the shared-folder URL as the stable remote entry point when the environment can open SharePoint/OneDrive shared links.
- Role: shared web-hard/workspace for large raw data and binary outputs such as TIFF, PPTX, ZIP, PDB/SDF, trajectory files, large CSVs, and export packages.

### OneDrive / SharePoint access gate

**Explicit denylist:** `kgene95@gmail.com` OneDrive. Do not access it at all for this skill, including search, list, read, write, upload, move, rename, metadata inspection, or fallback storage. If it is the active Microsoft/OneDrive connection, stop OneDrive operations immediately.

Before any OneDrive/SharePoint read/write that is meant to affect the canonical research workspace:

1. Prefer the canonical UST shared-folder URL above as the workspace entry point.
2. When an account identity is exposed, verify that the destination resolves to the UST shared workspace owned by `chskim@office.ust.ac.kr`.
3. Proceed only if the accessible workspace is the shared folder containing `LG_노트북/`, or if the user explicitly authorizes another destination for this operation.
4. If the active Microsoft/OneDrive identity is different, do **not** silently fall back to that drive and do **not** create a replacement `LG_노트북` folder there.
5. If the UST shared-folder URL cannot be opened in the current environment, report that limitation and continue with GitHub-only state updates when that still satisfies the task, or prepare a handoff artifact for later upload.
6. Treat any other connected OneDrive as non-canonical unless the user explicitly reassigns it. The explicit denylisted account `kgene95@gmail.com` remains inaccessible unless the user explicitly revokes this prohibition in a later instruction.

## Destination priority

For persistent cross-account continuity, prefer:

1. GitHub `kgene95/KIOM` for compact versioned memory/state.
2. UST OneDrive `LG_노트북/` for large files and shared binary artifacts.
3. AI-internal memory only as a convenience layer, never as the sole project record.

The purpose is portability across ChatGPT accounts, Work, Codex, terminal workflows, and other AI systems.
