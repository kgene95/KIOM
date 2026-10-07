---
name: run-network-pharmacology
description: "Run reproducible, source-traceable network pharmacology for compounds or extract constituents and a disease: chemical identity, broad target collection, disease targets, human species/stable-ID normalization, mapping QC, overlap, branch-aware PPI and hub analysis, GO/KEGG/Reactome enrichment, optional robustness analysis, evidence integration, docking-candidate recommendation, SCI publication figures, optional Cytoscape automation, checkpoints, computational-audit handoff, and final reporting. Use for de novo analysis, published-study reproduction or audit, NP figures/Fig. 2, and NP-to-docking handoff. Never execute docking; stop after a validated docking-ready recommendation."
---

# Run network pharmacology
## Start here: lightweight start, model escalation, and execution handoff

- Start the workflow in ordinary Chat or a fast/lower-cost model unless the user has already chosen a stronger reasoning model. Early intake, file inventory, metadata checks, deterministic extraction, routine formatting, scripted calculations, and straightforward QC usually do not justify a model upgrade.
- At the beginning of the run, tell the user once that the workflow can start in the current/lightweight model and that the Skill will explicitly recommend a stronger reasoning model when a listed scientific judgment checkpoint is reached. Do not repeatedly announce this during routine steps.
- At a listed checkpoint, briefly tell the user **before finalizing the consequential decision** that a stronger reasoning model is recommended and state the reason in one line. If the current model is already at an appropriate higher-reasoning level, continue without a redundant upgrade prompt.
- After the judgment is resolved, return routine deterministic work to the faster/lower-cost model when practical. Never rerun completed calculations, mutate a frozen branch, or change inputs merely because the model changed.

### Model-escalation checkpoints for this Skill

Recommend stronger reasoning at these points:

- compound-identity ambiguity or structure-sensitive isomer/protonation choices that alter downstream target retrieval.
- deciding whether the broad pool requires narrowing and which source-native rule is scientifically justified.
- reconciling materially conflicting compound-target or disease-target evidence across sources.
- STRING/enrichment mapping anomalies or identity corrections that could change the analyzed gene set.
- choosing the final primary/sensitivity/proxy branch or deciding whether robustness analysis changes interpretation.
- resolving materially different hub rankings or topology results across prespecified methods/thresholds.
- integrating enrichment with experimental evidence for mechanism interpretation.
- final docking-candidate selection from the frozen NP branch and experimental/structural evidence.

### Codex / MCP / terminal execution rules

- Maintain a **single-controller rule** for the same local PC, terminal, GUI application, project folder, or output files. Do not let Codex and MCP/Remote Desktop/another terminal automation manipulate the same resource concurrently.
- Before handing control of the same local resource to MCP, Remote Desktop, or another terminal controller, pause or disconnect Codex unless Codex itself is the sole controller executing that step. Save a checkpoint first.
- After launching a long-running external program or calculation, verify that it actually started and record the PID/job ID when available, log path, output path, command/config, and resume checkpoint.
- Recommend disconnecting/closing Codex while the external program runs **only after confirming the process is independent of the Codex session** and no active reasoning is required. Do not keep Codex connected merely to watch a GUI or wait for a calculation.
- If the calculation is a foreground or session-dependent process, **do not close Codex** because doing so may terminate the job. First detach it safely with a documented method or keep the controlling session open.
- When the external calculation or GUI step finishes, reconnect Codex only when needed for result parsing, QC, scientific interpretation, or the next deterministic command, and resume from the saved checkpoint rather than restarting the workflow.
- When the user asks for autonomous continuation or a completion alert for a genuine long-running calculation, create a lightweight heartbeat when the automation facility is available. Choose its interval from the recorded expected duration: 30 minutes for a roughly 20-minute–6-hour job, 2 hours for a roughly 6–24-hour job, and 6 hours for a multi-day job. Prefer a provider/job completion callback when one is available. Inspect only the PID/job state, designated log, and completion/error marker; remain silent while the job is healthy and progressing.
- Before launching a calculation expected to take hours or days, state the estimated duration, whether the estimate is based on a prior local run or a rough assumption, the monitoring interval, and that only completion, failure, unexpected stop, or a required decision will trigger a user-facing alert.
- Before waiting on a long calculation or external retrieval, inspect the checkpoint and identify two to four high-value tasks that are independent of the running process. Prioritize evidence/methods crosswalks, unresolved-access memos, figure specifications, reproducibility/handoff records, and next-stage feasibility planning. Explain the concrete outputs and start the appropriate tasks when the user asks to continue autonomously; use parallel agents only when the user authorizes delegation and the tasks have separate files/resources.
- Do not create busywork or touch the active job's input, output, terminal, GUI, or controller from a parallel task. Save each independent result in a distinct, documented file and report the completed outputs together with the calculation status.
- Notify the user only on completion, failure, unexpected stop, or required action. Do not rerun calculations, reread outputs, or emit routine progress messages during a healthy run. Delete the heartbeat after its terminal event.




## Load only the needed references

- Read [methods.md](references/methods.md) for every analysis.
- Read [execution-environments.md](references/execution-environments.md) before external retrieval, long-running jobs, or bulk local processing.
- Read [branches-and-evidence.md](references/branches-and-evidence.md) for branch creation, narrowing, sensitivity, proxy, or reproduction.
- Read [docking-candidate-selection.md](references/docking-candidate-selection.md) before recommending docking targets.
- Read [figures-and-handoff.md](references/figures-and-handoff.md) when the user requests an SCI/publication/NP figure, Fig. 2, pre-Cytoscape review draft, or cross-environment handoff.
- Read [cytoscape-automation.md](references/cytoscape-automation.md) before actual Cytoscape/cyREST execution.
- Read [enrichment-qc.md](references/enrichment-qc.md) before accepting enrichment as final or using it in figures/candidate selection.
- Read [auditor-handoff.md](references/auditor-handoff.md) when preparing independent computational review or manuscript audit.
- Read [output-contract.md](references/output-contract.md) before checkpoints, completion, or final reporting.
- Read [deterministic-scripts.md](references/deterministic-scripts.md) before running bundled scripts.

## Scientific workflow

`compound identity -> compound targets -> disease targets -> species/stable-ID normalization -> mapping QC -> overlap -> branch separation -> PPI -> hub analysis -> GO/KEGG/Reactome -> sensitivity/robustness when indicated -> evidence integration -> docking-candidate recommendation -> SCI figure when requested -> final NP report -> STOP`

For de novo work, collect broadly first, preserve source-native scores and evidence, perform identity/species/mapping QC, diagnose the broad overlap and network, and narrow one source-specific rule at a time only when the pool is too large or biologically diffuse. For reproduction, the published Methods override de novo defaults.

## Complete source-panel collection

Treat source collection as comprehensive, not convenience-selected. At analysis start, freeze the source registry, identity rules, organism, and access plan. Before overlap or network analysis, attempt every source in the registry that can accept the study inputs. Do not omit an accessible source merely because another source has already returned sufficient records.

Use the baseline registry below for small-molecule/extract constituent–disease analyses. Keep the registry in the run manifest so it can be expanded without embedding project-specific compounds, diseases, cutoffs, or prior results in this reusable Skill.

1. Collect entity-target evidence from PharmMapper, SuperPred, SEA, PubChem bioactivity/target records, and STITCH chemical-protein associations.
2. Collect disease-target evidence from GeneCards, OMIM, and TTD.
3. Preserve for every attempted source: raw export or response, exact query, access date, database/tool version or release, species, native score/rank, evidence type, and source record ID.
4. Record a login, CAPTCHA, rate limit, inaccessible endpoint, unsupported input, or no-result response as `not retrieved` with its reason. Do not substitute another source or treat the absence as negative evidence.
5. Before submitting to a source that requires an email address for job completion (including PharmMapper), determine that requirement from the source's submission form. If email is required, ask the user whether to use the run-specific secure `contact_email`, provide another address, or omit that source; do not submit until the user authorizes the choice. Never hard-code a personal address in this reusable Skill, raw exports, figures, or manuscript-facing outputs. Record only that the email-notification requirement was met and redact contact information from any shareable copy.
   After an authorized email-backed job is submitted, check the connected Gmail account for the provider's completion notice using the job ID and provider name. When the notice is received, retrieve the official result from its linked job page immediately, preserve the raw export and completion timestamp, and continue normalization/QC without waiting for another user message. If Gmail is unavailable, unconnected, delayed, or lacks a matching notice, record that status and check the provider's official job-status page; do not invent completion or use a nonofficial mirror.
6. Normalize retained records to reviewed human UniProt accessions and HGNC-approved symbols. Retain input IDs, aliases, mapping route, one-to-many mappings, unmapped records, species exclusions, and pre/post-mapping counts. Complete this QC before calculating overlap or submitting STRING.
7. Build the functional PPI from the QC-passed overlap using STRING. Preserve its mapping report and edge export and record release, organism, score threshold, submitted/mapped/excluded counts, nodes, and edges.
8. Retrieve OmniPath separately as a signaling/regulatory annotation. Keep this evidence overlay distinct from the STRING functional PPI; it must not silently add or remove genes from the overlap or PPI.
9. From the same frozen QC-passed set, complete topology analysis, GO Biological Process, Cellular Component, and Molecular Function, and KEGG enrichment before mechanism interpretation or candidate selection. Use g:Profiler when available and preserve its raw response/export; otherwise record the named enrichment service and reason for substitution. Record the tool/database release, query date, identifier-mapping count, background, multiple-testing method, threshold, term IDs, adjusted P values, and member genes.

Do not choose targets or docking candidates until the source-panel ledger, mapping-QC table, STRING results, OmniPath annotation, topology, GO BP/CC/MF, and KEGG outputs are complete. Make the final selection only after reviewing the full evidence matrix; report why supported targets were retained or not selected.

## Non-negotiable controls

1. Preserve raw exports, source-native score/rank, evidence type, species, query, access date, and source record ID.
2. Separate predicted, database-supported, directly measured, disease, experimental, and historical-manuscript evidence.
3. Normalize to stable human identities before deduplication; preserve aliases, unmapped rows, one-to-many mappings, exclusions, and provenance.
4. Compare submitted gene, mapped identifier, preferred name, species, and expected HGNC/UniProt identity before and after STRING/enrichment. Reject identity-changing automatic mappings and rerun downstream analysis on the corrected set.
5. Register every analyzed gene set as `primary`, `sensitivity`, `broad_exploratory`, or `proxy`. Never present proxy data as the primary disease set.
6. Do not tune thresholds to reproduce a historical count. Without the original raw data and methods, label the result `NOT INDEPENDENTLY REPRODUCED`.
7. Use actual STRING edges, hub scores/ranks, and enrichment rows. Do not invent genes, edges, scores, pathways, or relative values.
8. Base docking recommendations on integrated NP, experimental, and structural evidence—not hub degree alone—and cite the supporting frozen branch.
9. Never submit, calculate, or interpret molecular docking in this Skill. Provide a docking-ready handoff and stop.
10. For every executed branch, record the actual databases, software, versions or releases, access dates, parameters, and raw-output locations. Record an unavailable version explicitly; never infer one from the date or a default.
11. Keep project-specific compounds, disease, historical analyses, and comparison branches in the run configuration and manifest, not in this reusable Skill.
12. When Cytoscape, cytoHubba, or MCODE is not actually executed, use a named reproducible graph workflow and do not label its metrics, communities, or figures as Cytoscape, cytoHubba, or MCODE results.

## Run gates

### Start

Run `scripts/environment_check.py` when local/desktop execution, Cytoscape automation, or bulk deterministic processing may be used. Record only capabilities actually detected; a missing GUI-control path does not block terminal/cyREST automation when those capabilities are available.

Freeze the question, compound scope, disease ontology, organism, analysis mode, sources, native score meanings, and access plan. Ask for user input only when identity ambiguity, indispensable unavailable data, login/CAPTCHA/terms, or a required recipient email blocks the next step.

### Analyze

Preserve raw inputs before transformations. Use deterministic scripts for mechanical normalization, overlap, branch registration, narrowing audit, sensitivity matrices, checkpoints, manifests, and validation. Use scientific reasoning for identity ambiguity, evidence reconciliation, adaptive narrowing, mechanism interpretation, and final candidate assessment.

### Analyze with Cytoscape when available

When the user requests a Cytoscape-rendered PPI or the frozen figure plan calls for Cytoscape, use the exact frozen PPI tables and the procedure in `cytoscape-automation.md`. Prefer cyREST automation when available so import, layout, style mapping, and export are reproducible even if the GUI cannot be inspected directly. Cytoscape is visualization/graph tooling, not a license to alter branch membership or source values.

### Analyze STRING without Cytoscape

When the user asks for STRING-derived topology, modules, or enrichment without actual Cytoscape execution, retain the official STRING mapping and edge exports, then calculate only clearly named code-based metrics from those frozen edges. Record the graph library and version, directed/undirected treatment, edge-weight treatment, isolate policy, metric definitions, and community algorithm/parameters. Use degree as the default primary topology measure; treat other centrality or community analyses as corroborative unless prespecified. Cytoscape input files may be produced, but must be labelled as inputs rather than Cytoscape results. When more than one prespecified network/metric scenario is analyzed, summarize hub presence/rank stability with `scripts/hub_robustness.py`; do not create a composite hub score unless it was prespecified and scientifically justified.

### Validate enrichment and robustness

Before mechanism interpretation or candidate selection, run `scripts/enrichment_qc.py` on frozen enrichment tables and record background, correction method, database/tool version, detected columns, and structural QC status. Review semantic/gene-set redundancy separately. When thresholds, graph settings, or hub methods materially affect conclusions, preserve the scenarios and generate `hub_robustness.csv` from actual ranks.

### Select candidates

Review available manuscript, presentation, graph, animal, cell, WB, qPCR, ELISA, IHC, IF, apoptosis, and pathway-validation evidence when provided. Recommend normally two or three targets, clearly distinguishing primary, alternative, mechanistic secondary, and not-recommended candidates. Do not transfer hub status between branches.

### Produce figures

When triggered, first create one data-derived eight-panel composite review figure from frozen tables. Do not export individual panel files until the user approves the composite. After approval, record it, export the individual panels and final composite package, and mark the figure `SCI-final` only after all panel QA checks pass. Do not use image generation for quantitative networks, genes, edges, scores, or enrichment results.

### Decide on a pre-Cytoscape review draft

After validated NP analysis and before asking whether to draft NP Methods/Results/figure legend or delivering the docking-candidate recommendation, ask whether the user wants a visual-only `REVIEW_DRAFT` composite to guide later Cytoscape work. State that it is a pre-Cytoscape layout and styling draft, not a Cytoscape result or final publication figure. If the user declines, continue directly to the manuscript-writing and docking-candidate gates.

If the user requests the draft, use the existing frozen branch and the figure procedure in `figures-and-handoff.md`. Treat the work as visualization only: never rerun analysis, alter raw inputs, mutate frozen tables, replace source values, filter to improve appearance, or change counts, genes, edges, scores, ranks, GeneRatio, FDR, enrichment terms, or branch identity. A selected subset of already-enriched terms is allowed only when each displayed value is copied exactly from the frozen table and the selection rule is recorded. Keep Cytoscape input node/edge tables traceable to the same frozen PPI output. Record the draft as `REVIEW_DRAFT` and retain its plotting source, frozen plotting inputs, visual specification, and panel QA.

### Complete

Validate canonical files with `scripts/validate_np_completion.py`. Before creating any shareable or downloadable package, run `scripts/privacy_audit.py` and require a clean result. Prepare the evidence bundle described in `auditor-handoff.md` when independent computational review is requested or when NP will be integrated with docking/manuscript audit. The final report must summarize inputs, broad and final counts, branch decisions, mapping corrections, PPI/hub stability, enrichment, evidence limitations, docking candidates and rationale, and generated files. State `DOCKING_NOT_STARTED`.

### Preserve reproducibility and package outputs

Create `NP_manifest.json` at analysis start and update it atomically after every completed stage. It must be machine-readable and record: analysis start/completion timestamps; run question and mode; compounds and disease ontology; species; source registry and exact queries; database/tool releases or explicitly unavailable versions; access/search dates; native score/rank meanings; all cutoffs, background and multiple-testing parameters; mapping rules; branch lineage; graph/enrichment settings; raw, processed and final output paths; scripts/software versions; job IDs/statuses; and file checksums where practical. Pair it with a human-readable checkpoint, but do not make the checkpoint the sole provenance record.

Never store API keys, passwords, session cookies, personal email addresses, or other credentials in a manifest, raw-output package, logs, filenames, or report. Exclude or redact them before any handoff.

At handoff, ask the user to select one package profile: (1) `results_only` for final tables/figures/report, (2) `results_plus_manifest` for final outputs plus manifest/checkpoint, or (3) `results_manifest_raw` for final outputs, manifest/checkpoint, raw source exports, queries and deterministic scripts. Recommend profile 3 for manuscript submission, peer-review response, or reproducibility. Build packages with explicit branch labels; never merge historical/primary/supplementary branches into one unlabelled result set.

After NP analysis, the optional pre-Cytoscape decision and any requested `REVIEW_DRAFT` are complete, deliver the docking-candidate recommendation and show a short manuscript-readiness summary. Explicitly ask whether to draft the NP Methods, NP Results, and NP figure legend. Do not write those manuscript sections before the user approves. If approved, write them from the frozen outputs without waiting for docking results; keep docking findings out of the NP Results. Then provide the docking handoff and stop. If the user requests independent verification, provide the auditor handoff from the same frozen branch without rerunning or mutating NP.

## Autonomous completion rule

When the user authorizes a workflow, execute the skill's complete authorized scope through its defined completion gate without waiting for a separate confirmation at every intermediate step. Continue deterministic processing, QC, record updates, figure/document preparation, and reproducibility packaging until the skill's work is complete. Ask the user only when a genuinely consequential scientific judgment could change the conclusion, indispensable information or access is missing, an irreversible/destructive or external action requires authorization, or a critical error cannot be safely resolved. Do not ask merely because another defined step remains.

For long-running calculations or retrievals, verify that the job started, record its command/configuration, output path, checkpoint, and expected duration, set a lightweight completion/failure monitor when available, and continue independent authorized work while it runs. Notify the user only for completion, failure, unexpected stop, or a required decision. Never claim completion from elapsed time alone; verify the final files and logs.

