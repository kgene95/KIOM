# Bundled deterministic scripts

Most scripts use Python's standard library. `cytoscape_ppi.py` additionally requires `pandas` and the official `py4cytoscape` automation package plus a running Cytoscape/cyREST instance. Inspect `--help` before use. Scripts enforce structure and reproducibility; scientific identity and interpretation still require review.

| Script | Purpose |
| --- | --- |
| `normalize_targets.py` | merge compatible target tables, normalize symbols/whitespace, filter species, retain provenance and flag duplicates |
| `mapping_qc.py` | compare submitted, mapped, expected identity and species; emit PASS/unmapped/species/identity states |
| `overlap.py` | calculate compound unions, disease sets, per-compound overlap and exact gene lists from curated rows |
| `register_branch.py` | add or replace one branch-registry row using a frozen exact-gene table |
| `record_narrowing.py` | add or replace one lineage/audit row and calculate overlap/gained/lost genes |
| `sensitivity_analysis.py` | optional one-source cutoff robustness matrix; rejects unfiltered multi-source score columns |
| `checkpoint.py` | write JSON/Markdown recovery state with separate computation and save status |
| `build_manifest.py` | merge scientific metadata with analysis completion time, runtime, file hashes and script hashes |
| `validate_np_completion.py` | validate canonical files, v5 run metadata, source availability, branches, counts, mappings, narrowing and candidate schema |
| `validate_figure_package.py` | validate either the composite-only `REVIEW_DRAFT` or the approved A–H `SCI-final` package, frozen inputs, registered branches, outputs and panel QA |
| `environment_check.py` | detect local Python/R/Cytoscape-related capabilities and whether cyREST is reachable |
| `cytoscape_ppi.py` | import frozen PPI node/edge tables into a running Cytoscape via cyREST, apply recorded layout/style mappings, and export SVG |
| `hub_robustness.py` | summarize gene presence and rank stability across prespecified hub/network scenarios without inventing new scores |
| `enrichment_qc.py` | structurally validate enrichment columns/statistics and record background, correction method, tool, and database version |

## Input boundaries

`normalize_targets.py` expects a named gene column and optional species, stable ID, entity and source columns. When source schemas differ, transform copies into a canonical table without modifying raw exports. Deduplication occurs after the requested identity/species handling; excluded rows remain traceable.

`overlap.py` expects `kind,entity,gene,source,source_id`, where `kind` is `compound` or `disease`. It calculates sets but does not validate biological identity.

`mapping_qc.py` defaults to `submitted_gene,mapped_gene,expected_gene,species,expected_species`. Establish expected identities from authoritative records before running it.

`sensitivity_analysis.py` expects comparable numeric scores within one source. When a file contains multiple sources, provide the source column and selected source value. Do not apply one cutoff across unlike predictors or disease databases.

`register_branch.py` and `record_narrowing.py` use run-relative exact-gene files. Use `record_narrowing.py` with identical parent/child files and `changed_rule=none` when freezing an unchanged broad set as final.

`checkpoint.py` accepts repeated `--branch-gene BRANCH_ID=GENE` and pointers to the job ledger, mapping corrections and narrowing audit. Update it after every consequential change.

`build_manifest.py` does not infer missing scientific metadata. For contract v6, supply analysis start UTC, software/database inventories, actual parameters including explicit Cytoscape/robustness booleans, workflow, branches, rules, limitations and status in the seed JSON. It records the final manifest-generation time and uses it as completion time only for a completed run when no explicit completion time was supplied.

Run `validate_np_completion.py` only after canonical files and manifest are prepared. For a figure review, run `validate_figure_package.py` after the composite, `visual_spec.json`, plotting source and `figure_qa.csv` exist; individual panels must not yet exist. After explicit user approval, add the approval record, individual panels, final composite formats and caption, then run the validator again. A PASS validates structure and internal consistency, not biological truth or visual quality.

## Additional execution boundaries

`environment_check.py` performs no external database retrieval; it only inspects local capabilities and the local cyREST endpoint. `cytoscape_ppi.py` requires Cytoscape to be running and never changes the analytical gene/edge set. `hub_robustness.py` requires at least two already-computed scenarios and summarizes ranks/presence only. `enrichment_qc.py` validates structure and recorded metadata but does not determine biological truth or semantic redundancy.
