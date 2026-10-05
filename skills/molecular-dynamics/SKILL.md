---
name: molecular-dynamics
description: Run or review reproducible protein-ligand molecular dynamics, including GROMACS/Amber setup, minimization, NVT/NPT equilibration, production trajectories, QC, and manuscript-ready provenance. Use after a structurally validated starting complex; do not use for docking or network pharmacology.
---

# Molecular dynamics

## Scope and scientific boundary

Use MD to assess the behavior of a specified, modelled complex under explicitly recorded conditions. It does not establish binding, inhibition, target engagement, or an in-vivo mechanism.

This skill begins when docking has produced a documented candidate complex and handoff. NVT and NPT are MD equilibration stages, not docking validation. If the user is using docking only, preserve the docking handoff and do not launch MD setup or equilibration.

Start from a versioned, structurally validated complex. Preserve original docking/receptor files and create MD-specific copies; never overwrite raw structures or reinterpret a failed docking pose as MD-ready.

## Preflight gate

Before production MD, record the selected pose/seed, chain/protomer, missing-residue treatment, ligand identity and protonation state, solvent/ions, force fields, ligand parameterization route, software versions, hardware, and all MDP/control files.

- Resolve missing residues, alternate locations, cofactors, metals, phosphorylation, disulfides, termini, and ligand atom mapping before topology construction.
- Confirm the ligand topology, net charge, atom count/order, and coordinates match the intended structure. Do not silently substitute a differently protonated ligand.
- Require a converged solvated minimization and stable restrained NVT/NPT equilibration before production. Treat a fatal error, LINCS warning, NaN, unexplained energy instability, or failed density/temperature stabilization as a gate failure to investigate rather than bypass.
- Keep production MD unstarted until the equilibration QC decision is recorded, unless the user explicitly requests an automatic production run.

## Long-running execution and notifications

For every external MD stage, record the PID/job ID, command, log, checkpoint, expected output directory, and resume procedure. Read [long-running-jobs.md](references/long-running-jobs.md) before launching a calculation expected to run longer than about 20 minutes or when the user asks for autonomous continuation.

## Workflow

`validated complex → topology/parameter QC → solvation and ions → minimization → restrained NVT → restrained NPT → equilibration QC → production MD → trajectory QC/analysis → reproducibility and manuscript handoff`

Use a staged approach. Verify actual output/log evidence after each stage; do not infer completion from a submitted command or a file name. Analyze replicate trajectories and sensitivity cases only when scientifically warranted and within the user-approved scope.

## Completion and reporting

Record stage status atomically in a machine-readable manifest and human-readable checkpoint. Preserve control files, exact commands, logs, checkpoints, trajectory files, analyses, and hashes where practical. Report the modeled condition, achieved simulation time, QC findings, limitations, and the precise claim boundary.

For detailed GROMACS session handling, automatic completion monitoring, restart rules, and low-cost notification behavior, read [long-running-jobs.md](references/long-running-jobs.md).
