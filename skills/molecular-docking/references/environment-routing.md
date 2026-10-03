# Capability routing

Detect available executables, Python packages, filesystem persistence, current structure-record access and compute first. GUI visibility is not required. A Windows PowerShell/terminal session that can execute Vina and Python is sufficient for the core calculation path.

Prefer this order:
1. current local terminal/Codex environment with persistent writable storage and versioned Vina/Meeko/RDKit;
2. another authorized local machine or server reachable through an approved terminal/remote connector;
3. a reproducible cloud/container environment;
4. planning/handoff only when no executable environment is available.

General Chat can handle candidate selection, biological interpretation, manuscript comparison and writing. Local/Codex suits Vina, Meeko/OpenBabel/RDKit, deterministic batch jobs, coordinate parsing and RMSD. Work can help with current RCSB/PubChem retrieval and multistep file handling. These are capability preferences, not hard mode requirements.

Run `scripts/environment_check.py` before the first docking calculation in a new environment. Required for the default local Vina path: writable storage, `vina`, Python 3 and a receptor/ligand preparation route. RDKit is required for symmetry-aware SDF RMSD; ProLIF is optional for structured interaction fingerprints. If a required capability is missing, state exactly what is missing and create a handoff; never claim the computation was performed.

After calculations, redocking, QC, interactions and result tables, stay in the current environment when it can complete the requested work. If transfer is useful, hand off `docking_checkpoint_final.md`, `docking_manifest.json`, `receptor_selection.csv`, `redocking_validation.csv`, `docking_results.csv`, `interaction_summary.csv`, `manuscript_handoff.md`, and when audit is requested `auditor_handoff.json`.
