# Current status — 2026-10-04

## Primary objective

Revalidate the manuscript Fig. 3(B) computational result using human IKKβ `4KIK` chain B and vitexin-4″-O-glucoside.  This is a reproducibility and manuscript-readiness check, not experimental proof of binding.

## 4KIK status

| Item | Status | Evidence |
|---|---|---|
| Receptor selection and preparation | COMPLETE | `02_IKBKB_4KIK/redocking/4KIK_chain_B_rigid.pdbqt` |
| Native KSA redocking | PASS | symmetry-aware heavy-atom RMSD 0.3808 Å in `KSA_redocking_30A_symmetry_rmsd.csv` |
| Locked Vina test docking | COMPLETE | neutral vitexin and naringenin, three seeds each |
| Vitexin pose replicate consistency | PASS | direct-coordinate heavy-atom RMSD 0.0485–0.1088 Å |
| Naringenin pose replicate consistency | NOT_ASSESSED | required if the comparator is reported quantitatively |
| Interaction fingerprints | NOT_RUN | PLIP conversion route failed; 5 Å proximity is not a replacement |
| Clash, strain, pocket-occupancy QC | NOT_ASSESSED | must be completed or explicitly limited before paper-level closure |
| Protonation sensitivity interpretation | LIMITED | neutral is conditional; vitexin anionic explorations are incomplete and naringenin sensitivity is absent |
| Publication figure | PENDING | draft composition exists; no final export approved |

## Required next actions for paper-level 4KIK completion

1. Produce versioned interaction analysis for the top pose of each pre-specified seed, or document a validated technical limitation without filling in contacts by inference.
2. Evaluate naringenin seed consistency if it remains in a comparative result table.
3. Record pocket occupancy, protein-ligand clashes, and ligand-geometry/strain QC for each interpreted complex.
4. Define whether protonation sensitivity is needed for a comparative claim.  If it is, run the relevant pre-specified protomers with three seeds; otherwise restrict conclusions to conditional neutral-state results.
5. Reconcile `receptor_selection.csv`, result tables, manifests, and checkpoints with the actual PASS/NOT_ASSESSED states.
6. Obtain figure composition approval before publication-resolution export, then draft manuscript text only within the documented claim boundary.

## Separate COX-2 status

`5IKR` is BLOCKED before native ID8 redocking because the deposited COH cobalt metalloporphyrin lacks a reviewed local template and defensible Vina atom/scoring treatment.  Keep it blocked pending original-researcher clarification or an independently reviewed parameterization plan.
