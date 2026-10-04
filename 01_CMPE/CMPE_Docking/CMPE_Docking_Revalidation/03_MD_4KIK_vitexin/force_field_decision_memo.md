# Force-field and protonation decision memo

**Status:** Evidence review complete; final MD parameterization not yet selected.

## Proposed workflow to review

Use a mutually compatible AMBER-family workflow: an AMBER protein force field with GAFF2 ligand parameters and AM1-BCC partial charges. This is a candidate, not an executed parameterization.

## Why this is the provisional candidate

- A recent vitexin MD study used GROMACS with Amber14SB for the protein and GAFF/ACPYPE ligand topology preparation.
- A separate vitexin study assigned AM1-BCC charges and GAFF parameters, while determining protein residue protonation at pH 7.0.
- This keeps protein and ligand parameter conventions aligned and is practical for a GROMACS workflow.

## Protonation decision

The docking branch used neutral state-8. It may be retained as one MD starting state because it is the validated docking coordinate set, but it must not be declared the uniquely correct aqueous state.

Published discussion of vitexin describes phenolic hydroxyl groups as generally weakly ionizing near physiological pH. However, vendor/aggregator sources list a predicted pKa near 6.25 for the specific diglucoside. Those sources are insufficient to settle the state. Therefore:

1. Parameterize the neutral docking state as the primary reproducibility branch.
2. Generate one chemically specified mono-anionic sensitivity state only after locating the deprotonated atom and confirming the microstate with a pKa/protonation tool.
3. Do not compare the two states as if their Vina scores or force-field energies were direct binding affinities.

## Required checks before any GROMACS run

1. Preserve each raw docking PDB and work only on copies in `input/`.
2. Review the 4KIK chain-B residue protonation with a named pKa method and record the pH.
3. Generate a ligand topology using one named toolchain; record atom mapping, net charge, AM1-BCC output, GAFF2 version, and all parameter warnings.
4. Validate that ligand atom names in the coordinate PDB match the ligand topology exactly.
5. Inspect the minimized complex for geometry/strain before equilibration.
6. Start with minimization plus 100 ps restrained NVT and NPT. A production trajectory is blocked until those checks pass.

## References used for workflow selection

- Yan et al. (2025), *Antihyperuricemic Effect of Hawthorn Flavonoid Vitexin*, GROMACS 2024.03 with Amber14SB protein and GAFF/ACPYPE ligand preparation. https://pmc.ncbi.nlm.nih.gov/articles/PMC13239997/
- Li et al. (2020), *Purified Vitexin Compound 1 Inhibits UVA-Induced Cellular Senescence*, AM1-BCC charges and GAFF ligand topology; protein protonation evaluated at pH 7.0. https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2020.00691/full

These references describe precedents, not validation of the CMPE complex.
