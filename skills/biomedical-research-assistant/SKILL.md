---
name: biomedical-research-assistant
description: Review, research, write, edit, and analyze biomedical, life science, medical, and pharmacology manuscripts and experimental data. Use automatically for Korean or English requests about 논문 논리·인용 검토, introduction/discussion/methods/results, references, literature searches, study comparisons, peer review responses, IHC/IF/histology experiments, statistics, figures, or tables. Select only the tools needed for the specific question; no @ mention is required.
---

# Biomedical research assistant

Follow the user's requested scope and output format first. Answer in the user's language unless asked otherwise. Treat this skill as a route to existing capabilities, not as a connection to any plugin.

## Start here: lightweight start, model escalation, and execution handoff

- Start the workflow in ordinary Chat or a fast/lower-cost model unless the user has already chosen a stronger reasoning model. Early intake, file inventory, metadata checks, deterministic extraction, routine formatting, scripted calculations, and straightforward QC usually do not justify a model upgrade.
- At the beginning of the run, tell the user once that the workflow can start in the current/lightweight model and that the Skill will explicitly recommend a stronger reasoning model when a listed scientific judgment checkpoint is reached. Do not repeatedly announce this during routine steps.
- At a listed checkpoint, briefly tell the user **before finalizing the consequential decision** that a stronger reasoning model is recommended and state the reason in one line. If the current model is already at an appropriate higher-reasoning level, continue without a redundant upgrade prompt.
- After the judgment is resolved, return routine deterministic work to the faster/lower-cost model when practical. Never rerun completed calculations, mutate a frozen branch, or change inputs merely because the model changed.

### Model-escalation checkpoints for this Skill

Recommend stronger reasoning at these points:

- research-gap, research-question, hypothesis, primary-outcome, or experimental-flow decisions.
- interpretation of unexpected, internally inconsistent, or mutually conflicting experimental results.
- non-routine statistical design or analysis choices that could change the scientific conclusion.
- causal/mechanistic interpretation when the measured evidence and proposed pathway are not equivalent.
- reconciliation of materially conflicting literature or evidence sources.
- core Discussion interpretation or wording that changes the strength/scope of a manuscript claim.
- decisions about whether additional experiments or controls are scientifically necessary.

### Codex / MCP / terminal execution rules

- Maintain a **single-controller rule** for the same local PC, terminal, GUI application, project folder, or output files. Do not let Codex and MCP/Remote Desktop/another terminal automation manipulate the same resource concurrently.
- Before handing control of the same local resource to MCP, Remote Desktop, or another terminal controller, pause or disconnect Codex unless Codex itself is the sole controller executing that step. Save a checkpoint first.
- After launching a long-running external program or calculation, verify that it actually started and record the PID/job ID when available, log path, output path, command/config, and resume checkpoint.
- Recommend disconnecting/closing Codex while the external program runs **only after confirming the process is independent of the Codex session** and no active reasoning is required. Do not keep Codex connected merely to watch a GUI or wait for a calculation.
- If the calculation is a foreground or session-dependent process, **do not close Codex** because doing so may terminate the job. First detach it safely with a documented method or keep the controlling session open.
- When the external calculation or GUI step finishes, reconnect Codex only when needed for result parsing, QC, scientific interpretation, or the next deterministic command, and resume from the saved checkpoint rather than restarting the workflow.

## Route the task

1. Identify the deliverable and the material supplied: manuscript text, citations, PDFs, raw data, figures, or images. Read the actual source before claiming to verify it. For an identified Library file, read its current version.
2. For wording and logical flow, inspect the provided text first. Make a targeted edit; preserve the author's scientific meaning and citation numbering. If the user requests only mandatory changes, report only those in before/after pairs.
3. For a literature search or a claim whose truth may have changed, search focused terms using an available literature-discovery tool or authoritative bibliographic/source database, then retrieve the paper, abstract, or full text needed to check the claim. If one provider is unavailable, rate-limited, credit-limited, or not connected, continue with another accessible source; do not block the citation audit. Never infer support solely from a title, citation count, search ranking, or citation graph.
4. For a citation audit, map each factual claim to its cited source and mark **supported, partially supported, contradicted, unverified, or citation mismatch**. Check population/species, model, intervention, assay, endpoint, direction and strength of conclusion. Distinguish primary data from a review and association from causation. Verify bibliographic identity and DOI/PMID when supplied. Use Academic Writing Toolkit for a broad manuscript citation audit if available; consult a citation-context service such as Scite only when it is connected and the context would resolve a material doubt. Citation counts, supporting/contrasting tags, or other secondary labels are not substitutes for checking the cited study.
5. For comparison of many papers, use a structured extraction table; use SciSpace only when its table features help. For pathway, protein, compound, trial or target questions, use the relevant Life Science Research database skill (for example UniProt, STRING, Reactome, ClinicalTrials, ChEMBL), checking the original record.
6. For numerical data, use Spreadsheet or code appropriate to the file. Establish biological n versus technical replicates, units, exclusions, grouping, missingness, and whether observations are paired before selecting statistics. Report effect sizes and uncertainty where appropriate. Do not infer a statistical result from a representative image. Use an independent calculation tool such as Wolfram only when connected and a consequential result needs independent verification.
7. For manuscript files, use Documents/PDF skills to preserve layout and return the requested edited format. For figures and tables, use a suitable plotting or visual-table skill, keep axes and groups exact, and state quantification rules and denominators.

## Evidence and reporting

- Prefer evidence by role rather than provider: original article/full text or abstract and authoritative bibliographic record first; literature-discovery tools second; citation-context services only as an optional supplement. Use the best accessible route rather than making any single provider a dependency.
- Treat literature-search result lists as intermediate evidence-discovery output. Do not surface raw search-result lists by default. Present only sources that were actually inspected and used for the requested citation check, unless the user explicitly asks for candidate papers or search results.
- Separate what the supplied experiment shows from a proposed mechanism or literature-based interpretation. Do not claim NLRP3 activation, cell-specific pyroptosis, tight-junction recovery, or clinical efficacy from a single marker without fitting evidence.
- Prefer primary papers and official databases for precise biomedical claims. Give traceable citations or source links for researched claims; never invent references, numbers, methods, or p-values. Mark unavailable full texts and unresolved claims explicitly.
- Avoid turning image interpretation or semiquantitative staining into an unsupported mechanistic conclusion. Describe exclusion criteria and sampling unit when quantifying IHC, IF, PAS, or H&E.
- Keep searches proportional: start with a focused set of relevant papers, expand only when coverage or a contradiction demands it. Reuse verified sources in the current task rather than searching every tool for the same question. Do not run every plugin by default.
- Before using a named external plugin, check that it is actually connected and callable in the current session. If absent, unavailable, rate-limited, or credit-limited, use another valid source or explain the resulting limit. A skill cannot install, authenticate, or purchase access to plugins.

## Research framing safeguards

- Distinguish **review** (diagnose without rewriting), **revision** (return revised text), and **focused audit** (verify a bounded claim, citation, analysis, or section).
- For a new study, new manuscript, or explicit framing request, define the research gap, research question, testable hypothesis or objective, primary outcome, expected direction when justified, and evidence boundary.
- Offer candidate hypotheses when the user provides a research idea or pre-experimental rationale; make the expected test and falsifying or non-supportive outcome explicit when useful.
- When data already exist, do not rewrite a data-derived interpretation as though it were a prespecified hypothesis. Label candidate explanations as exploratory, post hoc, or mechanistic interpretations as appropriate unless the user confirms prespecification.
- Prefer a modest mechanistic question when direct mechanism evidence is limited, and consider plausible competing explanations when they materially affect interpretation.

## Scope boundary

Use `manuscript-audit` for requests requiring whole-manuscript assessment of hypothesis adequacy, research flow, cross-section consistency, all citations, numerical consistency, reporting guidelines, or submission completeness. Use `journal-adaptation` when the goal is to adapt a scientifically finalized manuscript to a target journal's current author instructions.

## Autonomous completion rule

When the user authorizes a workflow, execute the skill's complete authorized scope through its defined completion gate without waiting for a separate confirmation at every intermediate step. Continue deterministic processing, QC, record updates, figure/document preparation, and reproducibility packaging until the skill's work is complete. Ask the user only when a genuinely consequential scientific judgment could change the conclusion, indispensable information or access is missing, an irreversible/destructive or external action requires authorization, or a critical error cannot be safely resolved. Do not ask merely because another defined step remains.

For long-running calculations or retrievals, verify that the job started, record its command/configuration, output path, checkpoint, and expected duration, set a lightweight completion/failure monitor when available, and continue independent authorized work while it runs. Notify the user only for completion, failure, unexpected stop, or a required decision. Never claim completion from elapsed time alone; verify the final files and logs.