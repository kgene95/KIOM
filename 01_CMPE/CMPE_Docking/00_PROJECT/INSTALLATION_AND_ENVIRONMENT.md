# Local installation and environment guide

This record separates a repeatable **docking** environment from the optional **MD** environment. Install only the items needed for the current stage; do not install MD tooling before the docking result and receptor/ligand choice are fixed.

## Current project state

- 4KIK docking revalidation is complete; its interpretation remains `LIMITED` because it is conditional on the neutral ligand state.
- 5IKR is `BLOCKED`; software installation does not resolve its cobalt-metalloporphyrin parameterization issue.
- GROMACS was previously reported as installed in Ubuntu/WSL (CPU-only). In the present cloud session WSL enumeration returned access denied, so this must be confirmed in the user's own Ubuntu terminal.

## Install now: docking workflow

| Item | Purpose | Official download / documentation | Required |
| --- | --- | --- | --- |
| AutoDock Vina 1.2.7 | docking engine | <https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.7> | Yes |
| Miniforge | isolated scientific Python environment | <https://github.com/conda-forge/miniforge> | Yes |
| Meeko | ligand/receptor PDBQT preparation | <https://meeko.readthedocs.io/> | Yes |
| RDKit | chemical structure and QC utilities | <https://www.rdkit.org/docs/Install.html> | Yes |
| Open Babel | file conversion and structure checks | <https://openbabel.org/docs/Installation/install.html> | Recommended |
| UCSF ChimeraX | receptor/pocket/pose inspection and rendering | <https://www.cgl.ucsf.edu/chimerax/download.html> | Recommended |

### Conda environment after Miniforge installation

Open **Miniforge Prompt**, then run:

```powershell
conda create -n docking -c conda-forge python=3.11 meeko rdkit openbabel
conda activate docking
python -m pip install "vina==1.2.7"
```

This keeps Meeko, RDKit, Open Babel, and Vina in one named environment. Avoid installing them one-by-one into Windows system Python.

### Verification commands

```powershell
conda activate docking
python -c "import meeko, rdkit; from vina import Vina; print('Meeko/RDKit/Vina OK')"
obabel -V
```

For the standalone Vina archive, confirm the exact executable path with:

```powershell
& "C:\path\to\vina_1.2.7_win.exe" --version
```

## Install later: only when MD is approved

| Item | Purpose | Official page |
| --- | --- | --- |
| GROMACS | molecular dynamics engine | <https://www.gromacs.org/download/> |
| AmberTools | GAFF2/AM1-BCC ligand parameters for the proposed AMBER-compatible route | <https://ambermd.org/AmberTools.php> |
| ACPYPE (optional) | conversion helper; it does not replace force-field review | <https://github.com/alanwilter/acpype> |

MD should begin only after the neutral/charged-state decision and compatible protein-ligand force-field plan are documented. A docking score alone is not a sufficient reason to run MD.

### Ubuntu/WSL checks (run in the user's Ubuntu terminal)

```bash
gmx --version
conda --version
```

## Not necessary now

- PyMOL: optional; ChimeraX is sufficient for current receptor/pose QC and figure preparation.
- PLIP: the CMPE interaction fingerprint work is already completed. Install it only for a new interaction-analysis project.
- Cytoscape: needed for network pharmacology figures, not molecular docking execution.

## Before adding software

1. Do not delete or overwrite the existing Vina archive or completed CMPE outputs.
2. Keep downloads/installed programs outside the project data folders.
3. Record the version and verification output in the new project's manifest, not in completed CMPE results.

