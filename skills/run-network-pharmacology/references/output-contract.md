# Output, recovery, and completion contract

## Canonical files

| File | Minimum content |
| --- | --- |
| `NP_checkpoint.md` and `.json` | stage, computation/save status, exact branch sets, corrections, jobs, raw locations, pending items, next action |
| `job_ledger.csv` | service, URL/job ID, exact input, organism, submission/check times, parameters, status, retrieval, retries/failures |
| `compound_identity.csv` | exact names, stable identifiers/structures, stereochemistry, confidence and ambiguity |
| `source_availability.csv` | one row per attempted source with retrieval status, identity/species/export/score checks, source URL/job ID, access date, version, raw/normalized paths, SHA-256 values, union inclusion, branch and exclusion reason |
| `source_archive/` | immutable source-delivered CSV/TSV/ZIP/JSON/raw API responses when retrievable; never overwrite them with normalized analysis tables |
| `broad_target_pool.csv` | full normalized compound-target harvest derived separately from the source archive, with source-native score/rank, evidence class/subtype, species, provenance and QC state |
| `compound_targets.csv` | QC-normalized compound targets and branch membership without loss of broad provenance |
| `disease_targets.csv` | disease ID, stable target ID, source/evidence, native score/rank, species and rule |
| `overlap_primary.csv` | exact final-primary genes with compound and disease provenance |
| `overlap_sensitivity.csv` | optional exact robustness genes and changed rule |
| `branch_registry.csv` | exact branch class, lineage, rules, species, mapping state, count, gene file and permitted interpretation |
| `narrowing_audit.csv` | one row for each broad-to-final decision or narrowing edge |
| `mapping_corrections.csv` | submitted, mapped and expected identity, action, reason and downstream rerun status |
| `PPI_results.csv` | branch, settings, submitted/mapped/excluded counts, nodes, edges, isolates and hub method/results |
| `enrichment_results.csv` | branch, database/ontology, term, GeneRatio/count, adjusted P/FDR, members, background and method |
| `docking_candidate_handoff.csv` | integrated target assessment and recommendation; status remains `DOCKING_NOT_STARTED` |
| `NP_manifest.json` | workflow/contract version, analysis dates, software/database versions, parameters, frozen rules, exact branches/counts, runtime/scripts, checksums, limitations and status |
| `analysis_method_record.csv` | one row per actual database, web service, package, executable, or graph algorithm: name, category, role, version/release, access/execution date, parameters, raw output, status, and note |
| `hub_robustness.csv` | conditional summary of actual hub presence/rank stability across prespecified scenarios; required only when robustness scenarios are analyzed |
| `enrichment_qc.json` | structural enrichment QC with tool/database version, background, correction method, detected columns, and issues |
| `cytoscape_automation.json` | conditional record of actual cyREST import/layout/style/export when Cytoscape is used |

For new runs use `contract_version=6`; v3/v4/v5 remain valid for backward compatibility. Contract v6 retains the v5 source-availability/evidence and runtime requirements and also requires explicit enrichment QC plus conditional Cytoscape/hub-robustness provenance. Contract v5 requires `analysis_started_utc`, `analysis_completed_utc`, `runtime.python`, `runtime.platform`, nonempty `software_inventory`, `database_inventory`, and `analysis_parameters`. Each software row records at least `name,version,role`; record `command` and `executable_path` when applicable. If a version cannot be detected, record an explicit value such as `not detected` with the reason rather than leaving it blank. Each database row records `name,release_or_version,access_date`; if the source publishes no release, use an explicit value such as `not reported by source`, never a silent blank. For contract v6, set `analysis_parameters.cytoscape_used` and `analysis_parameters.hub_robustness_performed` explicitly to true/false; when true, the corresponding provenance files are required. For de novo work set `workflow_strategy=BROAD_FIRST_ADAPTIVE_NARROWING`. Keep legacy fields only for backward compatibility; the branch registry and manifest `branches` object are authoritative.

`analysis_method_record.csv` is mandatory for new runs. It is a concise, human-readable inventory synchronized with the manifest; it never substitutes for raw files or the fuller inventories. Include an optional resource such as OmniPath only if it was actually queried or used. For graph analysis, state the exact algorithm and implementation. A code-based community result must not be described as MCODE, and a code-based hub metric must not be described as cytoHubba.

`narrowing_audit.csv` must exist even when the broad set becomes final. Record a broad-to-final row with `changed_rule=none`, unchanged counts, reason, and `decision=freeze_as_final`.

## State and persistence

Use normalized base states `PENDING`, `FAILED`, and `COMPLETED`; an informative suffix is allowed. Never overwrite a retry, conformer, source version, or changed-input job row. Treat computation completion and file-save completion as separate gates.

Checkpoint immediately after external-result integration, compound/disease union change, overlap change, mapping correction, branch creation, narrowing decision, final-set selection, STRING/hub completion, enrichment completion, and docking-candidate selection. The checkpoint must allow another session to resume without reconstructing state from prose.

The manifest must record analysis start/completion UTC, files and SHA-256 hashes, script hashes/versions, runtime, every used software/database version or explicit unavailability statement, access dates/releases, actual parameters/configuration, exact rules, branch gene lists/counts, mapping corrections, failed/unavailable sources, pending items, and `NP_COMPLETE_DOCKING_NOT_STARTED`. Source-level provenance must also record source URL, job ID when applicable, collection/access date, source-native score/rank semantics, database/tool version, raw archive path, normalized derivative path, and hashes where practical. Use `UNVERIFIED` rather than guessing any expected URL, date, job, or version field that cannot be verified.

## Completion validation

Before final reporting verify:

- identity ambiguity is resolved or explicit;
- raw provenance and broad pools are preserved;
- species/stable-ID normalization and mapping QC are complete;
- every analyzed branch has an exact matching gene table;
- corrected mappings drive downstream PPI, hubs, enrichment, candidates, and figures;
- narrowing and sensitivity decisions are auditable;
- enrichment QC records the actual background/universe, correction method, tool/database version and structural checks;
- if Cytoscape was used, its automation/manual provenance is explicit and frozen analytical values were not mutated;
- when robustness scenarios were run, hub stability is reported from actual scenario ranks/presence rather than a fabricated composite score;
- docking candidates use the schema and rules in [docking-candidate-selection.md](docking-candidate-selection.md);
- required files are present, nonempty, internally consistent, and listed in the manifest;
- NP status is complete and docking status is not started.

Run `scripts/validate_np_completion.py RUN_DIR`. Structural validation does not replace scientific review. For independent computational review, prepare the evidence set in `auditor-handoff.md` from these same frozen outputs; absence must remain explicit rather than inferred.

## Final report

Report purpose and mode; identity; sources and failures; broad compound/disease pools; broad overlap; narrowing decision/steps; final set; main driver of count changes; mapping corrections; PPI settings and topology; hub method and stability; GO/KEGG/Reactome results; stable pathways and unstable hubs; evidence tiers; bounded mechanism hypothesis; docking candidates with tier, recommendation class, selection basis and limitations; generated files; and `DOCKING_NOT_STARTED`.

## Optional manuscript drafting gate

Treat manuscript prose as an optional post-analysis deliverable, not an automatic completion requirement. After the NP analysis, approved NP figure, and docking-candidate recommendation are complete:

1. summarize which frozen files and figure version are ready for writing;
2. ask explicitly whether the user wants the NP Methods, NP Results, and NP figure legend drafted or inserted into a supplied manuscript;
3. proceed only after an affirmative response; silence or a request to continue analysis is not approval.

When approved, derive every number, threshold, database/software version, access date, branch, exclusion, algorithm, parameter, statistical rule, and panel description from the actual frozen manifest, raw outputs, configuration, tables, `visual_spec.json`, `figure_qa.csv`, and final figure. Never copy a Skill default into Methods unless the run records verify that it was actually used. Keep Methods factual and reproducible, Results descriptive and bounded, and the legend self-contained for every panel. Do not introduce docking scores, poses, interactions, or conclusions into the NP Results. NP prose may be completed before docking because docking does not alter the frozen NP analysis. Mark it for later manuscript-level harmonization of transitions, Discussion, Abstract, Conclusion, numbering, and terminology after docking is complete.

Manuscript drafting is not tied to Work mode. Use the current authorized environment when it can access the frozen inputs and manuscript; transfer only for a missing capability or material file-access need.
