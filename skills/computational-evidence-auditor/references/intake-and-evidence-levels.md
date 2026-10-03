# Intake and evidence levels

## Preferred evidence, strongest to weakest

1. Raw source exports / receptor-ligand source structures / engine logs
2. Machine-readable manifests, checkpoints, configs, hashes
3. Processed canonical CSV/TSV/JSON tables
4. Figure source data and exported figures
5. Methods/Results/legends
6. Collaborator notes or narrative summaries

An audit can proceed with levels 3-6, but label the result `PARTIAL_EVIDENCE_AUDIT` or `MANUSCRIPT_ONLY_AUDIT` as appropriate.

## Minimum useful collaborator package

For NP, try to obtain: compound identities, source/target table, disease-target table or overlap genes, STRING/PPI node-edge output, hub table, enrichment table, target-selection table, Methods, Results, and relevant figures.

For docking, try to obtain: target/ligand identities, PDB ID/chain, docking engine, grid or binding-site description, score table, pose files or interaction table, redocking/RMSD if performed, Methods, Results, and figures.

Do not refuse an audit because some items are absent. State exactly what the missing evidence prevents you from verifying.

## Evidence coverage table

For each major stage, record:

`stage | supplied evidence | status | can verify | cannot verify | follow-up needed`

Use the five evidence classes defined in SKILL.md.
