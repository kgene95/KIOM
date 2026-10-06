# Pre-MD completion report — CMPE Fig. 3(B)

## Completed before production MD

- Human IKKβ `4KIK`, chain B receptor selection and preparation documented.
- Native KSA redocking passed with symmetry-aware heavy-atom RMSD `0.3808 Å`.
- Neutral vitexin and naringenin were run with three locked seeds; seedwise pose consistency passed.
- PLIP 3.0.1 interaction XML and seedwise interaction summaries were generated.
- Clash and 5 Å pocket-occupancy screens passed for the neutral top poses.
- Neutral-state interpretation and monoanion sensitivity runs were separated in the result tables.
- Original 3RZF/PyRx results were retained as historical comparators only.
- Isolated-ligand MMFF94 relaxation screening was completed for the three neutral seeds of both ligands. Results are diagnostic only.
- GROMACS 2025.4, AmberTools, ACPYPE, and Open Babel were checked; a provisional topology was built and `grompp` preprocessing succeeded.
- Docking-pose/clean-vitexin atom mapping was resolved: PDBQT `SMILES IDX` 42/42 element checks passed; exact PubChem graph was rebuilt as 72 explicit-H atoms; AM1-BCC charges were transferred; GAFF2 typing and `parmchk2` completed.
- All status, manifest, checkpoint, inventory, and MD handoff records were updated.

## Still gated

- Hydrogen coordinates were regenerated from the docking heavy-atom geometry; ACPYPE user-charge topology generation succeeded and standalone `gmx grompp` passed.
- The provisional Gasteiger topology is not acceptable for scientific MD conclusions.
- AM1-BCC succeeded for clean PubChem geometry and charge transfer to the mapped 72-atom docking-order molecule passed. Ligand-only heavy-atom-restrained steepest-descent plus conjugate-gradient minimization reached Fmax 9.825 kJ mol⁻¹ nm⁻¹.
- The mapped ligand was combined with 4KIK chain B and complex `grompp` passed with the net-charge warning documented. A 1000-step complex minimization and a 5000-step protein-restrained minimization were attempted; a soft-restraint follow-up reduced the steepest-descent Fmax to 103.9, but CG remained at 123.0. Pocket close-contact review is required and the complex minimization gate remains open.

The pre-MD gate remains closed at this safe boundary. The ligand parameterization is resolved, but the solvated complex minimization gate remains open.
- A GROMACS-native route under `03_MD_4KIK_vitexin/pre_md_qc/gmx_solvated/` generated a 1.0 nm dodecahedral TIP3P box with 118,545 waters and 12 sodium ions. The neutral 366,265-atom system passed `grompp`.
- The 5,000-step PME steepest-descent minimization did not pass: final Fmax was `5,751.0405 kJ mol⁻¹ nm⁻¹` on `GLU 510 CD` (atom 8218). The minimized coordinates remain diagnostic only.
- A local relaxation test that released GLU510 while restraining the rest of the protein also failed; the maximum force moved to `SER 544 C` (atom 8771) at `18,952.709 kJ mol⁻¹ nm⁻¹`. This indicates a broader receptor-preparation issue rather than one isolated atom.
- `pdb4amber` then identified a 14.3948 Å SER544–GLY545 coordinate discontinuity. A TER-separated LEaP rebuild reduced the unsolvated complex maximum force to 2,640.3345 after 500 steps and 3,663.7849 after 2,000 steps. This confirms the chain-break repair helped, but the force gate remains open because ASP573 CG is still problematic.
- The earlier failed-solvation route has no usable equilibration trajectory. The repaired loop branch later completed restrained NVT and NPT for 100 ps each without fatal/LINCS errors; pilot and production trajectories do not exist.
- COX-2/5IKR remains blocked pending defensible COH parameterization.

## 2026-10-05 corrected pre-MD completion update

This update supersedes the earlier receptor-minimization limitation for the neutral 4KIK–vitexin branch.  The deposited structure was re-audited, only the three internal missing segments (174–176, 373–375, and 551–557) were rebuilt with PDBFixer, and all retained deposited chain-B coordinates were verified unchanged (5,270 common atoms; 0.000 Å RMSD).  The rebuilt receptor retained SEP177/SEP181 and excluded KSA/crystallographic waters before LEaP.

The independent Amber14SB/phosaa14SB/GAFF2 topology had zero LEaP errors.  The neutralized GROMACS system contains 118,420 TIP3P waters before neutralization, 10 sodium ions, and 366,069 atoms after neutralization.  Its unrestrained PME steepest-descent minimization converged after 2,114 steps at Fmax 969.362 kJ mol⁻¹ nm⁻¹, meeting the written `emtol = 1000` criterion.  The pre-MD entry gate is therefore **PASS** for this explicit modeled-loop, neutral-vitexin starting structure.  Restrained NVT and NPT each completed for 100 ps without fatal/LINCS errors. Pilot and production MD remain intentionally unrun.

## Claim boundary

The completed work supports a reproducible, conditionally interpreted 4KIK docking revalidation. It does not establish direct binding, inhibition, or in vivo mechanism. MD can resume only after the charge/force-field and minimization gates pass.
