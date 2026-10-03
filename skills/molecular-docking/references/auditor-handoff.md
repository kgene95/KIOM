# Computational evidence auditor handoff

Use this handoff when independent review is requested or when docking results will be checked together with upstream NP/manuscript text.

Create `auditor_handoff.json` without rerunning analysis. Include only verified facts and paths:
- project/job IDs and target/ligand identities;
- upstream NP handoff reference/branch when applicable;
- receptor selection table and selected PDB/chain;
- protocol ID, preparation tools/versions, exact Vina engine/version and seeds;
- grid and search parameters;
- validation status and redocking RMSD with source files;
- docking result/pose tables and all-run summary;
- interaction table and method/status;
- figure paths/version when approved;
- Methods/Results/legend draft paths if they exist;
- unresolved issues, missing evidence and statements that cannot be independently verified.

Classify each expected evidence item as `verified`, `partially_verified`, `missing`, or `not_applicable`. Never infer absent values. The auditor may recommend rerunning a docking stage, but it must not silently modify frozen docking outputs.
