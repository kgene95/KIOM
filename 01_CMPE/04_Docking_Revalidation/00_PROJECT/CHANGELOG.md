# Change log

## 2026-10-04 — GitHub–OneDrive handoff instructions added

- Added `00_PROJECT/GITHUB_ONEDRIVE_HANDOFF.md` with repository roles, synchronization rules, current scientific state, and a copy-ready prompt for a general ChatGPT conversation.
- Kept raw calculations and the current `LIMITED`/`BLOCKED` interpretation states unchanged.

## 2026-10-04 — portable handoff layer added

- Added `00_PROJECT/README_AGENT.md`, `CURRENT_STATUS.md`, this change log, and a hash-based inventory generator for cross-account or cross-agent continuation.
- Added root-level manifest and checkpoint indexes.  They point to receptor-level calculation records and do not replace them.
- Preserved the 4KIK job's `LIMITED` interpretation state.  No scientific result was changed.

## 2026-10-03 — 4KIK revalidation run

- Selected human IKKβ `4KIK` chain B in place of historical *Xenopus* `3RZF` for the new analysis branch.
- Prepared the locked Vina 1.2.7 protocol and ran KSA native-ligand redocking.
- Obtained symmetry-aware heavy-atom RMSD 0.3808 Å for the selected KSA redocked pose (PASS at ≤2.0 Å).
- Docked neutral vitexin-4″-O-glucoside and naringenin with three independent seeds.  Preserved all outputs, scores, configs, and manifest hashes.
- Recorded vitexin seed pose consistency and 5 Å proximity QC.  Did not fabricate interaction fingerprints after the PLIP route failed.
- Blocked the separate 5IKR branch pending defensible COH cobalt-metalloporphyrin handling.
