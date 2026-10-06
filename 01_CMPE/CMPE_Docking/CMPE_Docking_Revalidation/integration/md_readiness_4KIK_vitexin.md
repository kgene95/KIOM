# MD readiness handoff — CMPE Fig. 3(B)

## Intended MD branch

The sole MD-preparation candidate from this revalidation is the human IKKβ `4KIK` chain B complex with vitexin-4″-O-glucoside (PubChem CID `56776173`). This choice follows the manuscript's NF-κB results and Fig. 3(B), where vitexin glucoside–IKKβ is the primary docking interpretation. Naringenin is a docking comparator and is not an MD priority. COX-2/5IKR is excluded because native-ligand redocking is blocked by unresolved COH metalloporphyrin treatment.

## Docking evidence supporting the handoff

- Native KSA redocking passed: symmetry-aware heavy-atom RMSD `0.3808 Å` using the locked 4KIK chain B Vina protocol.
- Neutral vitexin top poses from seeds `20261004`, `20261005`, and `20261006` reproduced the same pose family (heavy-atom RMSD `0.0485–0.1088 Å`).
- The top neutral vitexin scores were `-10.452`, `-10.442`, and `-10.458 kcal/mol`, respectively. These are Vina scores only, not affinities.
- PLIP 3.0.1 interaction XML, clash screening, and pocket-occupancy screening passed for each neutral top pose. No screened heavy-atom contact was below `1.5 Å`.

## Coordinate candidates

Use the three poses as a consistency set during MD setup. Do not select a pose only because it has the lowest Vina score.

| Seed | Coordinate source | Role |
| --- | --- | --- |
| 20261004 | `02_IKBKB_4KIK/test_ligand_docking/visualization_pdb/4KIK_vitexin_pose1_complex.pdb` | Current Fig. 3(B) representative coordinate |
| 20261005 | `02_IKBKB_4KIK/interaction_qc/plip_v301/vitexin_4_double_prime_O_glucoside_neutral_seed20261005_complex.pdb` | Replicate starting coordinate |
| 20261006 | `02_IKBKB_4KIK/interaction_qc/plip_v301/vitexin_4_double_prime_O_glucoside_neutral_seed20261006_complex.pdb` | Replicate starting coordinate |

## Before MD execution

1. Review the biologically relevant vitexin protonation/tautomer state for the selected solvent pH. The present poses are explicitly the neutral state-8 docking condition.
2. The candidate ligand workflow is now explicit: clean PubChem graph → AM1-BCC charges → GAFF2 atom typing → `parmchk2` bonded-term supplement. Inspect net charge and bonded terms before solvating.
3. Remove docking-only charges and convert the selected complex into a force-field-ready protein–ligand topology. Preserve the original docking coordinates unchanged.
4. Run minimization and short restrained equilibration before production MD. Compare ligand heavy-atom displacement, protein–ligand contacts, hydrogen bonds, and pocket retention across the three starting poses.
5. Treat MD as a stability/sampling analysis of the modelled complex. It cannot establish direct binding, inhibition, or the in vivo mechanism reported in the manuscript.

## Current limitation

GROMACS `2025.4` is installed in Ubuntu/WSL and the MD analysis environment is available. Atom mapping is PASS and the mapped molecule has a rebuilt 72-atom explicit-H graph, transferred clean-geometry AM1-BCC charges, GAFF2 atom types, and a `parmchk2` frcmod. Hydrogen coordinates were regenerated from docking heavy-atom geometry, ACPYPE user-charge topology generation succeeded, and ligand-only restrained minimization passed at Fmax 9.825 kJ mol⁻¹ nm⁻¹. A reproducible solvated GROMACS system was built with a 1.0 nm dodecahedral TIP3P box and 12 sodium ions; `grompp` passed for the neutral 366,265-atom system. Its 5,000-step PME minimization did not pass the Fmax 10 gate (final Fmax 5,751.0405 kJ mol⁻¹ nm⁻¹ on GLU 510 CD, atom 8218). Therefore no NVT, NPT, pilot trajectory, or production MD result is claimed. The isolated-ligand MMFF94 relaxation screen is recorded under `03_MD_4KIK_vitexin/pre_md_qc/ligand_strain_proxy/` as a diagnostic only.
 A local test releasing GLU510 while restraining the rest of the receptor failed as well, with the maximum force moving to SER544 C at 18,952.709 kJ mol⁻¹ nm⁻¹. The receptor preparation requires broader review before MD.
 `pdb4amber` found a 14.3948 Å SER544–GLY545 discontinuity. A TER-separated LEaP rebuild reduced the unsolvated maximum force substantially, but a 2,000-step test still ended at 3,663.7849 kJ mol⁻¹ nm⁻¹ on ASP573 CG. The repaired topology is therefore diagnostic only and is not MD-ready.

## 2026-10-05 corrected readiness status — supersedes the limitation above

The `pdb4amber` gap labels are renumbered identifiers and were not sufficient to assign a deposited residue pair.  Direct deposited-coordinate and sequence audits instead identified the internal chain-B omissions 174–176, 373–375, and 551–557.  SEP177 and SEP181 remain explicitly retained for phosaa14SB.

The candidate receptor `pre_md_qc/structure_repair/4KIK_chainB_internal_loops_pdbfixer_v2.pdb` models only these 13 internal residues.  It preserves all 5,270 retained deposited chain-B atoms with 0.000 Å RMSD and maximum displacement.  The associated Amber14SB/phosaa14SB/GAFF2 complex passed LEaP with zero errors.  A neutral, 366,069-atom, TIP3P-solvated GROMACS system with 10 sodium ions then passed unrestrained PME steepest-descent minimization at the predeclared `emtol = 1000` criterion: Fmax 969.362 kJ mol⁻¹ nm⁻¹ after 2,114 steps (force norm 9.905).

**MD-entry preparation is PASS for the neutral-vitexin loop-repaired model.**  This is a modeled-loop starting structure, not proof that the unresolved deposited loop conformations are experimentally known.  Restrained NVT and NPT each completed for 100 ps without fatal/LINCS errors; pilot and production MD remain unrun. Neutral-state interpretation remains conditional.
