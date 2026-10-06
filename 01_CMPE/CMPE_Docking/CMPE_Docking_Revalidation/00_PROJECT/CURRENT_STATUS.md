# Current status — 2026-10-05

## Primary objective

Revalidate the manuscript Fig. 3(B) computational result using human IKKβ `4KIK` chain B and vitexin-4″-O-glucoside.  This is a reproducibility and manuscript-readiness check, not experimental proof of binding.

## 4KIK status

| Item | Status | Evidence |
|---|---|---|
| Receptor selection and preparation | COMPLETE | `02_IKBKB_4KIK/redocking/4KIK_chain_B_rigid.pdbqt` |
| Native KSA redocking | PASS | symmetry-aware heavy-atom RMSD 0.3808 Å in `KSA_redocking_30A_symmetry_rmsd.csv` |
| Locked Vina test docking | COMPLETE | neutral vitexin and naringenin, three seeds each |
| Vitexin pose replicate consistency | PASS | direct-coordinate heavy-atom RMSD 0.0485–0.1088 Å |
| Naringenin pose replicate consistency | PASS | direct-coordinate heavy-atom RMSD 0.0201–0.0461 Å across three seeds |
| Interaction fingerprints | PASS | PLIP 3.0.1 XML generated for top pose of each ligand and seed |
| Clash, strain, pocket-occupancy QC | PASS for clash/pocket screen; strain not independently minimized | minimum protein distance 2.471–2.726 Å; zero heavy-atom contacts below 1.5 Å; 20/41 of 20/42 ligand heavy atoms within 5 Å |
| Protonation sensitivity interpretation | LIMITED | neutral is conditional; vitexin anionic explorations are incomplete and naringenin sensitivity is absent |
| Publication figure | PENDING | draft composition exists; no final export approved |

## Required next actions for paper-level 4KIK completion

1. The 4KIK–vitexin neutral pose family is staged as the sole MD-preparation branch in `03_MD_4KIK_vitexin`; its starting-coordinate set and MD prerequisites are in `integration/md_readiness_4KIK_vitexin.md`.
2. GROMACS 2025.4 is installed in the user's Ubuntu/WSL environment. The package is CPU-only. A provisional Amber14SB/phosaa14SB/GAFF2 system was built and grompp succeeded, but minimization was stopped at step 235 after repeated water-settle failures; no MD trajectory exists.
3. The docking-pose/clean-vitexin atom mapping is PASS: PDBQT `SMILES IDX` gives 42/42 heavy-atom element matches; the exact PubChem graph was rebuilt as 72 explicit-H atoms; clean AM1-BCC charges were transferred; GAFF2 typing and `parmchk2` completed. ACPYPE user-charge topology generation and standalone grompp passed. Ligand-only restrained steepest-descent/conjugate-gradient minimization reached Fmax 9.825. The 4KIK–vitexin complex minimization remains open: strong protein restraints stopped at Fmax 264.5 and soft restraints reduced it to 103.9 before CG remained at 123.0; pocket close-contact review is required.
4. During MD setup, review the biologically relevant vitexin protonation/tautomer state and choose a compatible ligand parameterization workflow. Do not generalize neutral-state docking results beyond this condition.
5. Perform an explicit ligand-strain/minimization check if a strain claim is needed; current QC is a clash and pocket-occupancy screen only.
6. Reconcile `receptor_selection.csv`, result tables, manifests, and checkpoints with the actual PASS/LIMITED states.
7. Obtain figure composition approval before publication-resolution export, then draft manuscript text only within the documented claim boundary.

8. A pre-MD MMFF94 isolated-ligand relaxation screen was completed for all three neutral seeds of vitexin and naringenin. It is recorded as a screening-only diagnostic and does not replace Amber/GAFF2 ligand-strain analysis.

### 2026-10-05 MD repair update

The clean-geometry AM1-BCC run completed and its charges were transferred to the mapped docking-order molecule. The remaining blocker is geometric relaxation/topology assembly around H29; no NVT/NPT or production MD has been run and no trajectory/stability claim is available.

### 2026-10-05 solvated minimization update

- The prior large Amber solvation attempt was stopped when topology writing stalled; its incomplete output is not used.
- A GROMACS-native pre-MD route succeeded through solvation and neutralization: 1.0 nm dodecahedral TIP3P box, 118,545 waters, 12 sodium ions, 366,265 atoms, and `grompp` PASS. Inputs and logs are in `03_MD_4KIK_vitexin/pre_md_qc/gmx_solvated/`.
- The 5,000-step PME steepest-descent minimization failed the force gate: final Fmax `5,751.0405 kJ mol^-1 nm^-1` on `GLU 510 CD` (atom 8218). No NVT, NPT, pilot, or production MD has been run.
- The project is complete to the safe pre-MD boundary, but is not MD-ready. Repair of the receptor/complex geometry and a passing solvated minimization are required before equilibration.
- A local relaxation test releasing GLU510 while restraining the rest of the protein also failed; the maximum force moved to SER544 C at `18,952.709 kJ mol^-1 nm^-1`. This indicates a broader receptor-preparation issue, so no single-residue coordinate edit was applied.
- `pdb4amber` identified a 14.3948 Å SER544–GLY545 coordinate discontinuity. A TER-separated LEaP rebuild reduced the unsolvated force substantially, but a 2,000-step test still ended at `3,663.7849 kJ mol^-1 nm^-1` on ASP573 CG. Further receptor standardization is required before MD.

## 2026-10-05 current MD-preparation status — supersedes older minimization entries

- The previous `pdb4amber` residue-label interpretation was corrected because that tool reports *renumbered* gap positions.  Direct source-structure and sequence audits identified only three internal chain-B omissions: 174–176, 373–375, and 551–557.
- The new loop-repaired receptor keeps SEP177/SEP181 and preserves 5,270 deposited chain-B atoms exactly (0.000 Å RMSD); it adds only the 13 missing internal residues.  KSA and crystallographic waters were excluded before topology construction.
- Amber14SB/phosaa14SB/GAFF2 topology construction passed with zero LEaP errors.  The solvated, neutral system has 118,420 TIP3P waters before neutralization, 10 sodium ions, and 366,069 atoms after neutralization.
- GROMACS 2025.4 unrestrained PME minimization converged in 2,114 steps at Fmax 969.362 kJ mol^-1 nm^-1 using the recorded standard criterion `emtol = 1000`.  **The neutral 4KIK–vitexin MD-entry preparation is PASS.**
- No NVT, NPT, pilot trajectory, production MD, or MD-derived stability/binding claim exists.  Any future MD result applies only to the modeled-loop, neutral-vitexin condition.

### 2026-10-05 NVT equilibration start

- Input validation passed in GROMACS 2025.4 using the loop-repaired, minimized system.  The corrected `ref-t` setting, custom `Protein_Ligand`/`Water_and_ions` temperature groups, and protein/SEP heavy-atom position restraints were all recognized.
- Restrained NVT equilibration is now running for 100 ps at 300 K in the WSL working directory.  NPT and production MD remain unstarted.  Completion requires log review for LINCS/NaN errors and temperature stability before NPT is prepared.
- A durable NPT gate is now waiting in WSL: it will create the NPT input and start the restrained 100 ps NPT calculation only after NVT reaches normal completion without a fatal or LINCS warning.  It does not start production MD.
- The gate also exports NVT/NPT trajectory, checkpoint, log, input, temperature, pressure, and density records into the project `equilibration` directory.  It writes `PRE_PRODUCTION_EQUILIBRATION_COMPLETE` only after NPT returns normally; production MD remains intentionally unstarted.
- `03_MD_4KIK_vitexin/planning/production_md_feasibility.md` records the measured CPU-only rate and shows that manuscript-scale production MD requires GPU/HPC rather than the local laptop.
- Independent work completed while NVT runs: `integration/fig3b_revalidation_crosswalk.md` gives the manuscript-safe Fig. 3(B) replacement plan, and `integration/cox2_coh_collaborator_query.md` gives the original-researcher query needed to resolve the separate 5IKR/COH block.

### Deferred storage cleanup

- The active NPT run and QC are terminal. The documented cleanup was completed after preserving final inputs, NVT/NPT outputs, logs, QC summaries, and environment records.
- Removed from the local project and synchronized OneDrive copy: `system_provisional_gasteiger_solvated`, `pre_md_qc/complex_mapped_amber_bcc.amb2gmx`, `pre_md_qc/gmx_solvated`, and `pre_md_qc/receptor_rebuild_pdb4amber/gmx_solvated_corrected`.
- The final `structure_repair/gmx_solvated_loop_repaired/equilibration` branch was retained. A refreshed `file_inventory.csv` records the post-cleanup state.

## 2026-10-06 NPT completion and pre-production QC

- Restrained NPT completed normally in GROMACS 2025.4 for 50,000 steps / 100 ps. The log ends with `Finished mdrun`; no fatal error, LINCS warning, or segmentation fault was detected.
- Thermodynamic summaries were exported from the complete 100 ps records: NVT temperature average 300.035 K; NPT temperature average 300.035 K; NPT pressure average 12.9838 bar; NPT density average 986.93 kg m^-3.
- NPT trajectory, checkpoint, final coordinate, TPR, energy, log, and exported XVG/summary files were copied to the project `equilibration` directory.
- `PRE_PRODUCTION_EQUILIBRATION_COMPLETE` is present. Production MD has not been started. The next decision is whether to move this validated starting state to GPU/HPC production planning; do not claim dynamic stability or binding from equilibration alone.

## Separate COX-2 status

`5IKR` is BLOCKED before native ID8 redocking because the deposited COH cobalt metalloporphyrin lacks a reviewed local template and defensible Vina atom/scoring treatment.  Keep it blocked pending original-researcher clarification or an independently reviewed parameterization plan.
