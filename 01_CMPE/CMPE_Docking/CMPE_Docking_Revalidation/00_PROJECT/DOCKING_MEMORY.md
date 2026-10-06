# CMPE docking revalidation memory

Updated: 2026-10-06 (KST)

## Project identity

- Material: CMPE / 참외껍질
- Project: CMPE docking revalidation
- Canonical local project root: `CMPE_Docking_Revalidation`
- Manuscript priority: Fig. 3(B), vitexin-4″-O-glucoside with human IKKβ
- This record is for continuation. Do not rerun completed docking stages without a documented reason.

## Fixed scientific decisions

- Historical IKKβ `3RZF` is not reused: it is a *Xenopus laevis* structure with construct/model limitations.
- Primary receptor: human IKKβ `4KIK`, chain B.
- Native redocking control: K-252a/KSA.
- Validation result: symmetry-aware heavy-atom RMSD `0.3808 Å`; pre-specified `≤2.0 Å` gate PASS.
- Primary test ligand: vitexin-4″-O-glucoside, PubChem CID `56776173`, InChIKey `NDSUKTASTPEKBX-LXXMDOISSA-N`.
- Comparator: naringenin, PubChem CID `439246`, InChIKey `FTVWIRXFELQLPI-ZDUSSCGKSA-N`.
- Vina: AutoDock Vina `1.2.7`; fixed receptor/grid; seeds `20261004`, `20261005`, `20261006`.
- Historical 3RZF/PyRx scores and contact labels remain historical only and must not be copied into the new interpretation.

## Completed docking/QC

- 4KIK chain-B receptor preparation and native KSA redocking: PASS.
- Neutral vitexin and naringenin docking: three seeds each completed.
- Pose replicate consistency: vitexin heavy-atom RMSD `0.0485–0.1088 Å`; naringenin `0.0201–0.0461 Å`.
- PLIP `3.0.1` interaction records: generated for top pose of each ligand/seed.
- Pocket/clash screen: PASS for the recorded scope; no heavy-atom contact below `1.5 Å`.
- Limitation: neutral-state results are conditional; vitexin anionic exploration and independent ligand-strain quantification remain incomplete.

## MD handoff state

- MD branch: `03_MD_4KIK_vitexin`.
- Loop-repaired chain-B receptor and GROMACS-native solvated minimization: PASS (`Fmax 969.362`, `emtol=1000`).
- System: Amber14SB/phosaa14SB/GAFF2, TIP3P water, neutralized with 10 Na+, 366,069 atoms.
- Restrained NVT was interrupted by loss of the WSL GROMACS process at about `93 ps` and was safely resumed from checkpoint; the final NVT log completed without a fatal/LINCS message.
- Restrained NPT completed normally on 2026-10-06: 50,000 steps / 100 ps, GROMACS 2025.4, with `Finished mdrun` and no fatal/LINCS/segmentation-fault message.
- Equilibration QC summaries: NVT temperature 300.035 K; NPT temperature 300.035 K; NPT pressure 12.9838 bar; NPT density 986.93 kg m^-3.
- The final NVT/NPT records and `PRE_PRODUCTION_EQUILIBRATION_COMPLETE` are in the project `equilibration` directory. Production MD has not started; the next step is a separate GPU/HPC production decision.

## Separate blocked branch

- COX-2 `5IKR` remains blocked before ID8 redocking because the deposited COH cobalt metalloporphyrin lacks a reviewed local template and defensible Vina atom/scoring treatment.
- Do not delete COH merely to force Vina compatibility. Obtain the original-researcher parameter/template information or complete an independently reviewed parameterization plan first.

## Continuation rules

- Use the CMPE project root only. Do not use `02_MGC/MGC_Docking` or any `CMOE` path for this work.
- Read this file, `CURRENT_STATUS.md`, `docking_manifest.json`, and `docking_checkpoint.md` before resuming.
- Preserve raw inputs and hashes; do not overwrite source material.
- Do not claim docking or MD proves binding, inhibition, target engagement, or pathway regulation.

## Deferred storage cleanup

- Some large MD/preparation files are still local to the laptop or have not yet synchronized to OneDrive. Treat the laptop working copy as active until the current NPT and its QC finish.
- After the active MD branch reaches a terminal state, perform a documented cleanup review before deleting anything: identify failed/abandoned preparation routes, duplicate solvated structures, oversized intermediate trajectories, and stale logs.
- Preserve the final receptor/ligand inputs, topology, MDP files, checkpoints, final logs, QC summaries, hashes, and a short record of each removed or archived item.
- Do not delete or archive active NPT files, the current WSL checkpoint, or any unsynchronized laptop output. The cleanup is a later task and must be recorded in `CURRENT_STATUS.md`, `CHANGELOG.md`, `file_inventory.csv`, and the OneDrive/GitHub handoff record.
