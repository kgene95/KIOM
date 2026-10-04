# Change log

## 2026-10-04 — 4KIK–vitexin MD preparation branch initialized

- Confirmed the user-installed Ubuntu/WSL GROMACS package: `2025.4-Ubuntu_2025.4-1`, CPU-only with OpenMP enabled.
- Added `03_MD_4KIK_vitexin` as a preparation-only downstream branch; it references rather than alters the three validated neutral-vitexin docking coordinates.
- Added an MD input manifest, checksum-producing staging script, and force-field-agnostic minimization/NVT/NPT templates. No force field, ligand topology, solvation, minimization, equilibration, or production MD calculation has been performed.
- Flagged ligand protonation and compatible protein–ligand force-field selection as required scientific decisions before execution.
- Added `03_MD_4KIK_vitexin/force_field_decision_memo.md`: AMBER-family/GAFF2-AM1-BCC is the candidate workflow for review; neutral and mono-anionic vitexin states remain separate MD branches until a named pKa/protonation method is recorded.

## 2026-10-04 — 4KIK pose and interaction QC completed

- Repaired the PLIP input route by generating Open Babel PDB complexes with preserved `UNL` ligand records.
- Generated PLIP 3.0.1 XML interaction fingerprints for vitexin and naringenin top poses across all three neutral-state seeds.
- Added all-ligand seedwise pose RMSD and clash/pocket QC. All six neutral top poses passed the heavy-atom clash screen; minimum protein distance was 2.471–2.726 Å.
- Kept the interpretation conditional on the neutral protonation state; ligand strain remains unquantified and 5IKR remains blocked.

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
# 2026-10-04 — MD-oriented handoff for Fig. 3(B)

- Selected the validated human IKKβ `4KIK` chain B–vitexin neutral pose family as the only MD-preparation branch.
- Added `integration/md_readiness_4KIK_vitexin.md` with the three consistent starting coordinates, evidence, force-field prerequisites, and claim boundary.
- Updated `integration/manuscript_handoff.md` to replace the obsolete PLIP limitation with the completed PLIP 3.0.1 seedwise interaction record.
