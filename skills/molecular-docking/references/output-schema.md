# Output contracts

Each receptor job directory: `docking_checkpoint.md`, `docking_manifest.json`, `receptor_selection.csv`, `redocking_validation.csv`, `docking_results.csv`, `interaction_summary.csv`, config, preserved inputs/outputs/logs and command metadata. Integration directory contains combined tables, previous-vs-current table, `manuscript_handoff.md`, `docking_checkpoint_final.md`, and when requested `auditor_handoff.json`.

Use manifest `schema_version: "2"` for new jobs; v1 remains valid for backward compatibility. In addition to `project`, `job_id`, `target`, `ligands`, `stage`, `completed_stages`, `validation_status`, `status`, `receptor`, `protocol`, `files`, `issues`, and `next_action`, v2 requires `analysis_started_utc`, `environment` (`python`,`platform`), and nonempty `software_inventory` from job creation. Require nonempty `database_inventory` from stage 2 onward and `analysis_completed_utc` when the job becomes `CLOSED`. Each software row records at least `name,version,role`, plus actual `command` and `executable_path` when applicable. Each database row records `name,release_or_version,access_date`; use explicit `not reported by source` when no release is published.

`protocol` records the actual protocol ID, engine/version, receptor/ligand preparation routes, grid, seeds, config path and parameters used, not Skill defaults. Every completed stage must have output evidence; validate hashes before skipping. Stage 6+ requires PASS or explicit LIMITED alternate validation. CLOSED requires stage 8 completed and its tables.

CSV minimum columns:
- `receptor_selection.csv`: target,gene,pdb,species,resolution,mutation,chain,native_ligand,binding_site,cofactor,reason_for_selection,limitations,source_date
- `redocking_validation.csv`: target,pdb,native_ligand,protocol_id,grid,best_score,rmsd,pose_rank,seed,validation_status,reference_file,pose_file,rmsd_method,notes
- `docking_results.csv`: target,ligand,protocol_id,best_score,pose_rank,seed,key_residues,h_bonds,hydrophobic_pi,pose_qc,validation_status,config,pose_file
- `interaction_summary.csv`: target,ligand,pose_rank,seed,h_bonds,hydrophobic,pi,salt_bridges,metal_cofactor,key_residues,pocket,method,criteria,consistency
- `previous_vs_current.csv`: target,ligand,previous_method,previous_score,current_method,current_score,interpretation

Figure: first produce one combined draft for layout/content review. After explicit composition approval, export individual panels and publication-resolution versions. Record verified figure facts, panel order, Methods/Results source facts, limitations and interpretation guardrails in `manuscript_handoff.md`. Do not invent unresolved values.

## Optional manuscript drafting gate

After all selected receptor jobs are CLOSED, integrated tables pass QC and the final docking figure is approved:
1. summarize validated inputs, protocols, result tables, figure version, limitations and unresolved items;
2. ask whether the user wants Docking Methods, Docking Results and the docking figure legend drafted or inserted into a supplied manuscript;
3. proceed only after an affirmative response.

When approved, write only from the actual manifest, raw outputs, config/protocol files, audits, redocking validation, complete docking/interaction tables, final figure and `manuscript_handoff.md`. Never copy a Skill default into Methods unless run records prove it was used. Results must distinguish validated computation from interpretation, report failed/limited jobs and avoid treating scores as binding proof.
