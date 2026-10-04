# CMPE docking revalidation — AI handoff guide

## Purpose

This directory records an independent revalidation of the historical CMPE docking figure, with the immediate manuscript priority being Fig. 3(B): vitexin-4″-O-glucoside docked to human IKKβ.  It is **not** a de novo network-pharmacology project and must not be used to recompute upstream NP results.

## Read in this order

1. `00_PROJECT/CURRENT_STATUS.md`
2. `docking_manifest.json` and `docking_checkpoint.md` at this directory root
3. `02_IKBKB_4KIK/docking_manifest.json` and its native-ligand redocking files
4. `integration/manuscript_handoff.md` and `integration/previous_vs_current.csv`
5. `00_PROJECT/file_inventory.csv` to check local copies before analysis

## Fixed scientific decisions

- Historical IKKβ receptor `3RZF` is not reused for the new analysis because it is a *Xenopus laevis* construct.  The revalidation receptor is human IKKβ `4KIK`, chain B.
- The protocol uses the K-252a (KSA) co-crystal ligand as native redocking control.  The locked 30 Å Vina protocol produced a symmetry-aware heavy-atom RMSD of **0.3808 Å**, passing the pre-specified ≤2.0 Å gate.
- The primary test ligand is vitexin-4″-O-glucoside (PubChem CID 56776173; InChIKey `NDSUKTASTPEKBX-LXXMDOISSA-N`).  Naringenin is a comparator, not the main Fig. 3(B) interpretation.
- 4KIK test docking used AutoDock Vina 1.2.7, a fixed receptor/grid, and seeds 20261004/20261005/20261006.  Do not change receptor, grid, preparation, tautomer/protomer, seed policy, or scoring settings while interpreting the existing branch.
- Historical 3RZF/PyRx scores and interaction labels are historical records only.  Do not copy their residue contacts, 2D interaction map, or claims into the 4KIK analysis.

## What is complete and what is not

The 4KIK native-ligand validation and Vina docking runs are complete.  The 4KIK job must still be described as `LIMITED` until pose-QC and interaction-analysis records are complete or a defensible inability to run them is documented.  See `CURRENT_STATUS.md`.

COX-2/5IKR is a separate blocked branch: its deposited COH cobalt metalloporphyrin must not be deleted simply to enable Vina.  Do not run 5IKR test-ligand docking until a reviewed COH template and Vina-compatible cobalt treatment exist.

## Required working rules

- Treat `00_source/` and historical manuscript source material as read-only.
- Preserve raw inputs, PDBQT outputs, Vina logs, configs, hashes, and seed labels.
- Do not state that docking proves binding, target engagement, inhibition, or pathway regulation.
- Do not invent hydrogen bonds, π contacts, interaction fingerprints, or a 2D map when a tool does not produce them.
- Update the receptor manifest, root checkpoint, `CURRENT_STATUS.md`, `CHANGELOG.md`, and `file_inventory.csv` after any new calculation or QC decision.
- Before manuscript wording or publication figure export, report PASS/FAIL, exact method/version, unresolved limitations, and the permitted claim boundary.

## Figure status

`02_IKBKB_4KIK/figure_drafts/Fig3B_4KIK_vitexin_COMPOSITION_DRAFT_v2.png` is a review composition only.  It preserves the original whole-structure/callout/inset visual grammar, but the right panel is a 3D 4KIK pocket view rather than the historical 3RZF 2D interaction map.  It is not a final publication figure.
