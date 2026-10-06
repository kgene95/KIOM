# Restrained NPT QC summary

- Date: 2026-10-06 KST
- Engine: GROMACS 2025.4 (CPU-only WSL Ubuntu)
- System: loop-repaired human IKKβ 4KIK chain B–neutral vitexin complex; Amber14SB/phosaa14SB/GAFF2; TIP3P; 10 Na+; 366,069 atoms
- Stage: position-restrained NPT, 50,000 steps / 100 ps
- Termination: `Finished mdrun`; no fatal error, LINCS warning, or segmentation fault detected

## Thermodynamic summaries

| Observable | Mean | RMSD | Source |
|---|---:|---:|---|
| NVT temperature | 300.035 K | 0.542 K | `nvt_temperature_summary.txt` |
| NPT temperature | 300.035 K | 0.542 K | `npt_temperature_summary.txt` |
| NPT pressure | 12.9838 bar | 195.216 bar | `npt_pressure_summary.txt` |
| NPT density | 986.93 kg m^-3 | 0.9099 kg m^-3 | `npt_density_summary.txt` |

This is an equilibration/pre-production QC record. It does not establish production-trajectory stability, binding, inhibition, or target engagement. Production MD has not been started.
