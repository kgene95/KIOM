# 4KIK–vitexin MD preparation

This folder is the downstream MD branch for Fig. 3(B). It is based only on the validated human IKKβ `4KIK` chain B neutral-vitexin pose family. It does not contain an MD result yet.

## Starting structures

The three seed poses are retained as a consistency set. The 20261004 pose is the current figure representative; do not choose it solely because it is the displayed pose.

| Seed | Source coordinate | Purpose |
| --- | --- | --- |
| 20261004 | `02_IKBKB_4KIK/test_ligand_docking/visualization_pdb/4KIK_vitexin_pose1_complex.pdb` | Figure representative |
| 20261005 | `02_IKBKB_4KIK/interaction_qc/plip_v301/vitexin_4_double_prime_O_glucoside_neutral_seed20261005_complex.pdb` | MD replicate candidate |
| 20261006 | `02_IKBKB_4KIK/interaction_qc/plip_v301/vitexin_4_double_prime_O_glucoside_neutral_seed20261006_complex.pdb` | MD replicate candidate |

## Current software state

- GROMACS 2025.4 is installed in the user's Ubuntu/WSL terminal.
- The installed package is CPU-only (`GPU support: disabled`).
- No ligand parameterization tool or compatible protein–ligand topology has been installed or selected.

## Required scientific decision before executing MD

The neutral docking state must be reviewed against the intended solvent pH, then one mutually compatible protein and ligand force-field workflow must be selected. This is a consequential choice and is intentionally not guessed by the staging script.

The recommended candidate for review is an AMBER-compatible workflow: a current AMBER protein force field with GAFF2/AM1-BCC ligand parameters. The resulting ligand charge, atom types, bonded terms, and 1–4 scaling must be checked before it is combined with the protein topology.

## Safe next action

From the `CMPE_Docking_Revalidation` project root inside Ubuntu, run:

```bash
bash 03_MD_4KIK_vitexin/scripts/stage_inputs.sh
```

This only copies the three source PDB files into `03_MD_4KIK_vitexin/input/` and writes SHA-256 checksums. It does not alter docking files or start an MD calculation.
