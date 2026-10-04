# Project storage and handoff

Use this reference whenever a docking job is resumed from, synchronized to, or handed off through OneDrive, GitHub, or another shared project store.

## Canonical-root preflight

Before any folder creation, upload, move, rename, overwrite, or deletion:

1. Identify the canonical project root from the user's current path or explicit project instructions. Do not infer it from a ligand, receptor, or archive filename.
2. Read the root listing and enumerate existing child folders and files. When the destination is nested, inspect each parent and search the exact target name in the available inventory, manifest, or archive index.
3. Reuse an existing exact-match folder. Do not create a second folder with a similar name such as a receptor-specific, handoff-specific, or date-suffixed variant unless the user explicitly requests a new branch.
4. Treat a prior conversation summary, stale screenshot, or local archive as a hint only; verify the live destination before writing.
5. After a write, verify the resulting item at the exact destination and record the path in the project checkpoint.

If the live structure and local inventory disagree, pause mutations and report the mismatch. Read-only inventory and comparison may continue.

## Active files versus archives

- Keep active raw inputs and generated analysis files in the canonical project folders so later work can add files without rebuilding an archive.
- Use archives as optional snapshots or transfer artifacts, not as the active working directory. Do not require an archive to be regenerated for every new result unless the user asks for a refreshed snapshot.
- Never delete, overwrite, or replace an archive or existing project folder without explicit authorization for that exact action.
- Preserve raw inputs and generated results in separate clearly named subfolders; never mix a new result into a raw-input folder.

## OneDrive and GitHub roles

- OneDrive is the source of record for large raw structures, PDB/PDBQT/SDF files, logs, figures, and active analysis outputs.
- GitHub is the versioned record for manifests, checkpoints, scripts, small CSV/Markdown tables, and reproducibility documentation. Confirm the repository and target path before committing or pushing.
- Keep OneDrive and GitHub paths in the manifest or handoff document. Record the synchronization date and whether large binaries were excluded from GitHub.
- After updating either store, verify the visible result and report the exact path or commit; do not claim synchronization from a local copy alone.

## Canonical alignment and cleanup

When the GitHub tree and OneDrive tree disagree, do not copy the GitHub tree blindly. Read the workspace index and the OneDrive project root, then make the GitHub control tree use the same material, project, package, and branch names. Keep raw and large files in OneDrive, and keep their paths and hashes in GitHub. Move valid small records and scripts to the canonical path with a Git move commit so history is preserved. Remove practice skeletons and duplicate project paths only in an explicit cleanup commit; never remove the reusable `skills/` directory. After cleanup, compare both trees again and update the project README, status, changelog, inventory, and handoff records.
