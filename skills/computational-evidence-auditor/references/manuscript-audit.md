# Manuscript audit

## Methods

Every material parameter must be either supported by evidence or explicitly marked missing. Check source/database/tool names, versions/releases if available, access dates, organism, cutoffs, mapping rules, STRING settings, enrichment correction, PDB/chain, docking engine, grid/pocket, search settings, seed, validation method, RMSD, and interaction-analysis method.

Do not repair an incomplete Methods section by guessing defaults.

## Results

Every numeric result and named entity should trace to supplied output. Check counts, genes, hubs, pathways, adjusted P values, docking scores, RMSD, residues, and figure references.

Use restrained language:
- `identified as a highly connected node` rather than `the key therapeutic target` when evidence is topology only.
- `enriched in pathways related to ...` rather than `activated/inhibited the pathway` without experimental directionality.
- `showed a predicted docking score of ...` rather than `had high binding affinity` for Vina scores alone.
- `suggested a plausible binding pose` rather than `confirmed binding`.

## Discussion and conclusions

Separate computational hypothesis generation from experimental confirmation. Identify which claims are supported by network inference, structural modeling, prior literature, and the study's own experiments.

## Figures and legends

Verify that legends identify the analysis represented, branch/threshold when scientifically relevant, and meaning of visual encodings. Do not call code-derived networks Cytoscape/cytoHubba/MCODE outputs unless those tools were actually executed.
