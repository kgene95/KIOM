# NVT reproduction record

## Environment

- OS layer: Ubuntu on WSL2
- Conda environment: `cmpe-md`
- Environment export: `environment.yml`
- GROMACS: `2025.4-Ubuntu_2025.4_1`, CPU-only, thread-MPI, SSE4.1
- ACPYPE: `2026.9.4`
- AmberTools: `26.0`
- Python: `3.14.7`
- Force-field preparation: Amber14SB/phosaa14SB for protein and GAFF2/ACPYPE for vitexin; TIP3P water; 10 Na+

## NVT inputs

- `nvt_restrained.mdp`: requested NVT settings
- `nvt_grompp_effective.mdp`: effective settings recorded by GROMACS
- `nvt.tpr`: compiled run input
- `nvt_prev.cpt`: checkpoint before the resumed segment
- `nvt.cpt`: final checkpoint
- `nvt.gro`: final coordinates
- `nvt.log`: complete GROMACS log

The final NVT segment was resumed from approximately 92.2 ps using the checkpoint and completed the 100 ps target. The resume command was:

```text
gmx mdrun -deffnm nvt -ntomp 4 -pin on -cpi nvt.cpt -append
```

The initial NVT input was compiled with the loop-repaired solvated structure, equilibration topology, index file, and the restrained NVT MDP. The final log contains normal completion and no fatal/LINCS/segmentation-fault message.

## File integrity

SHA-256 values for the final NVT files are recorded in `file_inventory.csv` and should be checked before reuse.

This record documents equilibration reproducibility. It is not a production-MD stability or binding claim.
