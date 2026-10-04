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
| Naringenin pose replicate consistency | PASS | direct-coordinate heavy-atom RMSD 0.0201–0.0461 Å across three seeds |
| Interaction fingerprints | PASS | PLIP 3.0.1 XML generated for top pose of each ligand and seed |
| Clash, strain, pocket-occupancy QC | PASS for clash/pocket screen; strain not independently minimized | minimum protein distance 2.471–2.726 Å; zero heavy-atom contacts below 1.5 Å; 20/41 of 20/42 ligand heavy atoms within 5 Å |
| Protonation sensitivity interpretation | LIMITED | neutral is conditional; vitexin anionic explorations are incomplete and naringenin sensitivity is absent |
| Publication figure | PENDING | draft composition exists; no final export approved |

## Required next actions for paper-level 4KIK completion

1. Decide whether the paper will report only the conditional neutral-state results or add three-seed charged-state sensitivity runs; do not generalize beyond the selected state.
2. Perform an explicit ligand-strain/minimization check if a strain claim is needed; current QC is a clash and pocket-occupancy screen only.
3. Reconcile `receptor_selection.csv`, result tables, manifests, and checkpoints with the actual PASS/LIMITED states.
4. Obtain figure composition approval before publication-resolution export, then draft manuscript text only within the documented claim boundary.

## Separate COX-2 status

`5IKR` is BLOCKED before native ID8 redocking because the deposited COH cobalt metalloporphyrin lacks a reviewed local template and defensible Vina atom/scoring treatment.  Keep it blocked pending original-researcher clarification or an independently reviewed parameterization plan.
