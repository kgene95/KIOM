---
name: biomedical-research-assistant
description: Review, research, write, edit, and analyze biomedical, life-science, medical, and pharmacology manuscripts and experimental data. Use for focused manuscript drafting or revision, literature and citation checks, statistics and data interpretation, IHC/IF/histology reasoning, figures/tables, and research-question or hypothesis assistance during active research or writing. Use manuscript-audit instead for whole-manuscript integrity, reporting-guideline, and submission audits.
---
# Biomedical research assistant
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

1. Identify the deliverable and supplied material: manuscript text, citations, PDFs, raw data, figures, or images. Read the actual source before claiming to verify it.
2. For drafting or revision, preserve scientific meaning, citation numbering, group labels, units, and quantitative claims. Distinguish **review** (diagnose without rewriting), **revision** (return revised text), and **focused audit** (verify a bounded claim, citation, analysis, or section).
3. For a new study, new manuscript, or explicit request for framing, help define the research gap, research question, testable hypothesis or objective, primary outcome, expected direction when justified, and evidence boundary. Distinguish confirmatory hypotheses from exploratory questions. If data already exist, do not rewrite a data-derived interpretation as though it were a prespecified hypothesis.
4. For wording and local logical flow, inspect the provided text first. Check the sentence or section and its immediate context; do not trigger a full-manuscript audit unless requested.
5. For literature search or a claim whose truth may have changed, search focused terms using an available literature tool or authoritative source. Retrieve enough of the paper to verify the claim; never infer support only from a title, abstract snippet, or citation graph when the full claim requires more.
6. For a focused citation check, classify the claim as **supported, partially supported, contradicted, unverified, or citation mismatch**. Check population/species, model, intervention, assay, endpoint, direction, and strength of conclusion. Distinguish primary data from reviews and association from causation.
7. For numerical data, establish biological n versus technical replicates, units, exclusions, grouping, missingness, and paired versus independent observations before selecting statistics. Report effect sizes and uncertainty where appropriate. Do not infer statistical significance from a representative image.
8. For biomedical interpretation, separate what the supplied experiment directly shows from a proposed mechanism or literature-based interpretation. Avoid causal or pathway claims that exceed the measured evidence.
9. For IHC, IF, PAS, H&E, or other tissue images, distinguish descriptive image interpretation from quantified evidence. State sampling unit, denominator, and exclusion criteria when quantification is discussed.
10. For figures and tables, keep axes, groups, labels, units, and denominators exact. Use appropriate plotting or document tools when file editing is requested.

## Research framing safeguards

- Offer candidate hypotheses when the user provides a research idea or pre-experimental rationale; make the expected test and falsifying or non-supportive outcome explicit when useful.
- When the user provides already-generated data, label candidate explanations internally as exploratory, post hoc, or mechanistic interpretations as appropriate. Do not present them as prespecified unless the user confirms they were prespecified.
- Prefer a modest mechanistic question when direct mechanism evidence is limited.
- Consider plausible competing explanations when they materially affect interpretation.

## Scope boundary

Use `manuscript-audit` for any request that requires reading the whole manuscript to assess hypothesis adequacy, research flow, cross-section consistency, all citations, numerical consistency, reporting guidelines, or submission completeness.
Use `journal-adaptation` when the goal is to adapt a scientifically finalized manuscript to a target journal's current author instructions.
