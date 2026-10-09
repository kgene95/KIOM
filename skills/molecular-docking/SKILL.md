---
name: molecular-docking
description: Perform reproducible ligand-target molecular docking from validated candidates or an NP handoff, including receptor/ligand identity audit, local terminal capability routing, receptor and ligand preparation, native-ligand redocking validation, conventional AutoDock Vina docking, pose/interaction QC, reproducibility manifests, figures, and manuscript handoff. Use for new docking, independent reanalysis, validation, resuming a docking project, or preparing docking-ready outputs. Never recompute upstream network pharmacology.
---

# Molecular docking
## Start here: lightweight start, model escalation, and execution handoff

- Start the workflow in ordinary Chat or a fast/lower-cost model unless the user has already chosen a stronger reasoning model. Early intake, file inventory, metadata checks, deterministic extraction, routine formatting, scripted calculations, and straightforward QC usually do not justify a model upgrade.
- At the beginning of the run, tell the user once that the workflow can start in the current/lightweight model and that the Skill will explicitly recommend a stronger reasoning model when a listed scientific judgment checkpoint is reached. Do not repeatedly announce this during routine steps.
- At a listed checkpoint, briefly tell the user **before finalizing the consequential decision** that a stronger reasoning model is recommended and state the reason in one line. If the current model is already at an appropriate higher-reasoning level, continue without a redundant upgrade prompt.
- After the judgment is resolved, return routine deterministic work to the faster/lower-cost model when practical. Never rerun completed calculations, mutate a frozen branch, or change inputs merely because the model changed.

### Model-escalation checkpoints for this Skill

Recommend stronger reasoning at these points:

- final receptor/PDB selection, especially when several structures differ in species, construct, resolution, state, or bound ligand.
- mutation/construct, chain, protomer, missing-residue, alternate-location, or binding-site integrity decisions.
- cofactor, metal, heme/prosthetic-group, water, protonation, or charge-handling decisions that can affect docking validity.
- native-ligand redocking that is borderline, fails, or requires a protocol/grid change.
- grid or protocol changes made after validation evidence is reviewed.
- conflict between docking score and structural plausibility, strain, clashes, or interaction geometry.
- cross-receptor interpretation and final prioritization of complexes for downstream MD.
- reconciliation of a new validated docking result with a historical manuscript result that would change Methods, Results, figures, or conclusions.

### Codex / MCP / terminal execution rules

- Maintain a **single-controller rule** for the same local PC, terminal, GUI application, project folder, or output files. Do not let Codex and MCP/Remote Desktop/another terminal automation manipulate the same resource concurrently.
- Before handing control of the same local resource to MCP, Remote Desktop, or another terminal controller, pause or disconnect Codex unless Codex itself is the sole controller executing that step. Save a checkpoint first.
- After launching a long-running external program or calculation, verify that it actually started and record the PID/job ID when available, log path, output path, command/config, and resume checkpoint.
- Recommend disconnecting/closing Codex while the external program runs **only after confirming the process is independent of the Codex session** and no active reasoning is required. Do not keep Codex connected merely to watch a GUI or wait for a calculation.
- If the calculation is a foreground or session-dependent process, **do not close Codex** because doing so may terminate the job. First detach it safely with a documented method or keep the controlling session open.
- When the external calculation or GUI step finishes, reconnect Codex only when needed for result parsing, QC, scientific interpretation, or the next deterministic command, and resume from the saved checkpoint rather than restarting the workflow.
- When the user asks for autonomous continuation or a completion alert for a genuine long-running calculation, create a lightweight heartbeat when the automation facility is available. Choose its interval from the recorded expected duration: 30 minutes for a roughly 20-minute–6-hour job, 2 hours for a roughly 6–24-hour job, and 6 hours for a multi-day job. Prefer a provider/job completion callback when one is available. Inspect only the PID/job state, designated log, and completion/error marker; remain silent while the job is healthy and progressing.
- Before launching a calculation expected to take hours or days, state the estimated duration, whether the estimate is based on a prior local run or a rough assumption, the monitoring interval, and that only completion, failure, unexpected stop, or a required decision will trigger a user-facing alert.
- Before waiting on a long calculation, inspect the checkpoint and identify two to four high-value tasks that are independent of the running process. Prioritize manuscript/result crosswalks, unresolved-issue memos, figure specifications, reproducibility/handoff records, and next-stage feasibility planning. Explain the concrete outputs and start the appropriate tasks when the user asks to continue autonomously; use parallel agents only when the user authorizes delegation and the tasks have separate files/resources.
- Do not create busywork or touch the active job's input, output, terminal, GUI, or controller from a parallel task. Save each independent result in a distinct, documented file and report the completed outputs together with the calculation status.
- Notify the user only on completion, failure, unexpected stop, or required action. Do not rerun calculations, reread outputs, or emit routine progress messages during a healthy run. Delete the heartbeat after its terminal event.




1. Inspect `docking_checkpoint.md` and `docking_manifest.json` first, then relevant result CSVs. Resume completed stages from verified outputs; do not reread full NP/manuscript/raw structures unless a specific question requires them. Audit input candidates and local capability with `scripts/environment_check.py`. Read [workflow](references/workflow.md) and [environment routing](references/environment-routing.md).
2. Route execution by capability, not interface. Prefer a local terminal/PowerShell/Codex environment when it can execute versioned Vina, Meeko/OpenBabel, RDKit and optional ProLIF. GUI visibility is not required. If the current ChatGPT surface cannot access the execution environment, create a deterministic handoff rather than pretending calculations were run.
3. Create one independent job per receptor. Read [receptor QC](references/receptor-qc.md) and [ligand QC](references/ligand-qc.md); when RDKit is available, also apply [RDKit-assisted ligand QC](references/rdkit-ligand-qc.md) for deterministic identity, stereochemistry, valence and atom-mapping checks. Record three distinct selection evidence axes (NP, experimental/mechanistic, structural). Accept NP docking-ready handoff without recomputing NP. Check live structure records when selecting PDBs; record date, source, and rejected alternatives.
4. Lock preparation, grid, engine version, random seeds, and output paths before calculations. Read [Vina protocol](references/vina-protocol.md). Preserve config files, source IDs and hashes. Never silently substitute a ligand isomer, chain, cofactor, preparation method, or binding site.
5. Prepare receptor and ligands with deterministic command wrappers when the required tools are available. Use `scripts/prepare_receptor.py` and `scripts/prepare_ligand.py` or an explicitly documented equivalent. Record exact commands, tool versions, input/output hashes, protonation/charge assumptions and failures.
6. Redock a native ligand when available before any test ligand. Use `scripts/run_vina.py` for the engine call and `scripts/calculate_rmsd.py` for same-frame heavy-atom RMSD after a validated coordinate conversion. Apply [validation gate](references/redocking-validation.md). A failed protocol blocks test docking on that receptor; unavailable native ligand requires an explicit alternate validation plan and limitation, never a fabricated PASS.
7. For validated jobs, run conventional docking using the locked protocol. Execute all prespecified seeds/replicates, retain all poses and logs, summarize outputs with `scripts/summarize_vina.py`, and analyze pose, score, strain, clashes, interactions and consistency. Read [interpretation](references/interpretation.md) and [interaction analysis](references/interaction-analysis.md). Use GNINA or other secondary methods only as independent sensitivity/pose support, never as a replacement for a failed Vina validation gate and never compare confidence scores directly with Vina kcal/mol.
8. After each stage, update the job checkpoint and machine-readable manifest atomically and validate with `scripts/validate_manifest.py`; verify listed output files and hashes before skipping work. Close each receptor job only after validation, docking and QC records exist. Integrate CLOSED jobs from CSVs, not raw reruns. Use [output schema](references/output-schema.md).
9. Build a combined docking figure for review; export individual panels and publication-resolution files only after the user confirms composition. Once docking, QC and the approved figure are complete, summarize manuscript readiness and explicitly ask whether to draft Docking Methods, Docking Results and the docking figure legend. Never frame docking as proof of binding, engagement, inhibition or pathway regulation.
10. When the user requests independent verification, peer-review-style checking, or provides a colleague's partial NP/docking package, create the auditor handoff defined in [auditor handoff](references/auditor-handoff.md). Do not rerun upstream NP unless explicitly requested in the NP skill; do not fill missing evidence by assumption.

## Boundary with molecular dynamics

The docking workflow ends after receptor/ligand QC, native-ligand redocking, test-ligand pose and interaction QC, reproducibility records, and docking/manuscript handoff. Candidate prioritization may identify a complex for downstream MD, but docking does not include solvation, minimization, NVT, NPT, production trajectories, or trajectory analysis. Those stages belong to the separate `molecular-dynamics` skill and require an explicit MD handoff. Do not start NVT/NPT merely to complete a docking result.

## Project storage and handoff

When the workflow touches OneDrive, GitHub, or another shared project store, read [project storage and handoff](references/storage-handoff.md) before any external write. When a local OneDrive-synchronized root exists, inventory and update that local root first; use the OneDrive web UI only when local synchronization is unavailable, broken, or needs a post-sync visibility check. The live project root must be inventoried before creating or uploading anything; existing exact-match folders are reused, and archives are optional snapshots rather than active working directories. Verify each write at its exact destination and record the path or commit in the checkpoint.

## Project identity and continuation records

Before any shared-folder operation, read [project identity and continuation records](references/project-continuation.md). Confirm the material, project root, analysis package, and analysis branch as separate names. Read the workspace index and the nearest project status file before using a path; never infer a material from a storage-category folder name. Keep `PROJECT_README.md`/`README_AGENT.md`, `CURRENT_STATUS.md`, `CHANGELOG.md`, `file_inventory.csv`, `GITHUB_ONEDRIVE_HANDOFF.md`, and branch-level `FOLDER_STATUS.md` current. New project-level or analysis-branch folders must receive a generated `FOLDER_STATUS.md` and a changelog/index entry in the same operation. A new account or agent must resume from these records and checkpoints instead of rerunning completed calculations.

## Reproducibility manifest and package handoff

Create `docking_manifest.json` and a human-readable checkpoint before receptor preparation, then update both atomically after every stage. Record engine and version, environment, executable paths, receptor source/PDB ID and retrieval date, chain and preparation decisions, ligand identity/stereochemistry/protonation, grid coordinates and dimensions, search parameters, random seeds, validation control and redocking RMSD, failure/alternate-validation decisions, all result paths, score/pose-selection rules, interaction-analysis method, raw output paths, exact commands and file checksums where practical.

Never store API keys, passwords, cookies, personal email addresses or other credentials in manifests, checkpoints, package filenames, logs or reports. Exclude or redact them before handoff.

At docking handoff, ask the user to select: (1) `results_only`, (2) `results_plus_manifest`, or (3) `results_manifest_raw`. Recommend profile 3 for a manuscript, peer-review response, independent rerun or reproducibility archive. In profile 3 retain receptor/ligand source files when redistribution is permitted, preparation/configuration files, redocking controls, logs, poses, interaction tables, scripts and checksums. If a source structure cannot be redistributed, retain its source identifier, retrieval date, lawful hash and retrieval instructions instead. Never mix receptor jobs or unrelated study branches without explicit labels.

## Execution scripts

Scripts are deterministic helpers around external engines; they do not replace the docking engine.

- `scripts/environment_check.py`: inventory local terminal capabilities and versions.
- `scripts/prepare_receptor.py`: run a detected Meeko receptor-preparation command and record provenance.
- `scripts/prepare_ligand.py`: run a detected Meeko ligand-preparation command and record provenance.
- `scripts/run_vina.py`: execute AutoDock Vina from a locked config, seed and explicit receptor/ligand inputs; save command/log metadata.
- `scripts/calculate_rmsd.py`: same-frame heavy-atom RMSD for redocking validation.
- `scripts/summarize_vina.py`: extract every Vina pose score to CSV.
- `scripts/analyze_interactions.py`: inventory/optionally run a versioned interaction-analysis path when ProLIF dependencies are available; otherwise fail clearly and preserve the limitation.
- `scripts/validate_manifest.py`: validate stage state, provenance and hashes.

Read `--help` before use. Never claim a script or external program ran unless an actual output/log from that execution exists.

## Autonomous completion rule

When the user authorizes a workflow, execute the skill's complete authorized scope through its defined completion gate without waiting for a separate confirmation at every intermediate step. Continue deterministic processing, QC, record updates, figure/document preparation, and reproducibility packaging until the skill's work is complete. Ask the user only when a genuinely consequential scientific judgment could change the conclusion, indispensable information or access is missing, an irreversible/destructive or external action requires authorization, or a critical error cannot be safely resolved. Do not ask merely because another defined step remains.

For long-running calculations or retrievals, verify that the job started, record its command/configuration, output path, checkpoint, and expected duration, set a lightweight completion/failure monitor when available, and continue independent authorized work while it runs. Notify the user only for completion, failure, unexpected stop, or a required decision. Never claim completion from elapsed time alone; verify the final files and logs.

