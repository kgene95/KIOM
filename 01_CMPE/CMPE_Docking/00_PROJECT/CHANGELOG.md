# Change log

## 2026-10-05 - installation and environment guide added

- Added `INSTALLATION_AND_ENVIRONMENT.md` with stage-specific official download links, verification commands, and the boundary between docking and later MD setup.
- Recorded that the present cloud session cannot enumerate WSL because of access control; this is not evidence that the user's reported GROMACS installation was removed.
- No docking, MD, or scientific result was rerun or changed.

## 2026-10-04 ? 4KIK pose and interaction QC completed

- Repaired the PLIP input route by generating Open Babel PDB complexes with preserved `UNL` ligand records.
- Generated PLIP 3.0.1 XML interaction fingerprints for vitexin and naringenin top poses across all three neutral-state seeds.
- Added all-ligand seedwise pose RMSD and clash/pocket QC. All six neutral top poses passed the heavy-atom clash screen; minimum protein distance was 2.471?2.726 A.
- Kept the interpretation conditional on the neutral protonation state; ligand strain remains unquantified and 5IKR remains blocked.

## 2026-10-04 ? GitHub?OneDrive handoff instructions added

- Added `00_PROJECT/GITHUB_ONEDRIVE_HANDOFF.md` with repository roles, synchronization rules, current scientific state, and a copy-ready prompt for a general ChatGPT conversation.
- Kept raw calculations and the current `LIMITED`/`BLOCKED` interpretation states unchanged.

## 2026-10-04 ? portable handoff layer added

- Added `00_PROJECT/README_AGENT.md`, `CURRENT_STATUS.md`, this change log, and a hash-based inventory generator for cross-account or cross-agent continuation.
- Added root-level manifest and checkpoint indexes.  They point to receptor-level calculation records and do not replace them.
- Preserved the 4KIK job's `LIMITED` interpretation state.  No scientific result was changed.

## 2026-10-03 ? 4KIK revalidation run

- Selected human IKK�� `4KIK` chain B in place of historical *Xenopus* `3RZF` for the new analysis branch.
- Prepared the locked Vina 1.2.7 protocol and ran KSA native-ligand redocking.
- Obtained symmetry-aware heavy-atom RMSD 0.3808 A for the selected KSA redocked pose (PASS at ��2.0 A).
- Docked neutral vitexin-4��-O-glucoside and naringenin with three independent seeds.  Preserved all outputs, scores, configs, and manifest hashes.
- Recorded vitexin seed pose consistency and 5 A proximity QC.  Did not fabricate interaction fingerprints after the PLIP route failed.
- Blocked the separate 5IKR branch pending defensible COH cobalt-metalloporphyrin handling.

