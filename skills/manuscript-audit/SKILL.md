---
name: manuscript-audit
description: Perform whole-manuscript scientific integrity and submission-readiness audits for biomedical, medical, pharmacology, and life-science papers. Use after a draft substantially exists or when the user asks to review the entire study logic, hypothesis, research flow, cross-section consistency, citations, numerical consistency, reporting guidelines such as ARRIVE/CONSORT/STROBE/PRISMA, or submission completeness. Do not use for ordinary sentence editing or routine drafting.
---
# Manuscript audit
## Start here: lightweight start, model escalation, and execution handoff

- Start the workflow in ordinary Chat or a fast/lower-cost model unless the user has already chosen a stronger reasoning model. Early intake, file inventory, metadata checks, deterministic extraction, routine formatting, scripted calculations, and straightforward QC usually do not justify a model upgrade.
- At the beginning of the run, tell the user once that the workflow can start in the current/lightweight model and that the Skill will explicitly recommend a stronger reasoning model when a listed scientific judgment checkpoint is reached. Do not repeatedly announce this during routine steps.
- At a listed checkpoint, briefly tell the user **before finalizing the consequential decision** that a stronger reasoning model is recommended and state the reason in one line. If the current model is already at an appropriate higher-reasoning level, continue without a redundant upgrade prompt.
- After the judgment is resolved, return routine deterministic work to the faster/lower-cost model when practical. Never rerun completed calculations, mutate a frozen branch, or change inputs merely because the model changed.

### Model-escalation checkpoints for this Skill

Recommend stronger reasoning at these points:

- judging whether the study hypothesis/objective and overall research logic are scientifically adequate.
- resolving major Introduction-Methods-Results-Discussion alignment problems.
- judging whether a central claim is stronger than the actual evidence.
- resolving material conflicts among figures, tables, text, statistics, or supplementary results.
- interpreting results that are statistically consistent but biologically or mechanistically ambiguous.
- prioritizing major-revision-level scientific changes or deciding which weaknesses materially affect submission readiness.

### Codex / MCP / terminal execution rules

- Maintain a **single-controller rule** for the same local PC, terminal, GUI application, project folder, or output files. Do not let Codex and MCP/Remote Desktop/another terminal automation manipulate the same resource concurrently.
- Before handing control of the same local resource to MCP, Remote Desktop, or another terminal controller, pause or disconnect Codex unless Codex itself is the sole controller executing that step. Save a checkpoint first.
- After launching a long-running external program or calculation, verify that it actually started and record the PID/job ID when available, log path, output path, command/config, and resume checkpoint.
- Recommend disconnecting/closing Codex while the external program runs **only after confirming the process is independent of the Codex session** and no active reasoning is required. Do not keep Codex connected merely to watch a GUI or wait for a calculation.
- If the calculation is a foreground or session-dependent process, **do not close Codex** because doing so may terminate the job. First detach it safely with a documented method or keep the controlling session open.
- When the external calculation or GUI step finishes, reconnect Codex only when needed for result parsing, QC, scientific interpretation, or the next deterministic command, and resume from the saved checkpoint rather than restarting the workflow.

## Audit workflow

1. Establish scope and version. Read the whole manuscript and relevant figures/tables/supplements when available.
2. Run the **research logic audit** in `references/research-logic.md`.
3. Run the **cross-section and evidence audit** in `references/integrity-audit.md`.
4. When quantitative facts recur across sections, build `consistency_manifest.csv` using `references/consistency-schema.md`, then run `scripts/check_consistency.py`.
5. Identify the study design and apply the relevant reporting guideline gate in `references/reporting-guidelines.md`. Use current official guideline sources when details may have changed.
6. Run the submission-completeness checks in `references/submission-audit.md`.
7. Return findings before performing extensive revision unless the user explicitly asked for direct correction.

## Required distinctions

- Distinguish **prespecified hypothesis**, **exploratory question**, and **post hoc/mechanistic interpretation**. If the manuscript does not document prespecification, do not assume it.
- Distinguish what the experiment directly supports from literature-based interpretation.
- Distinguish absence of reporting from absence of performance. For example, "randomization not reported" is not the same as "randomization not performed".
- Treat association, pathway involvement, target engagement, and causal mechanism as different evidentiary levels.

## Default report

Classify findings as:
- **Critical**: threatens validity, traceability, or a central conclusion.
- **Major**: materially weakens logic, evidence alignment, reporting, or reproducibility.
- **Minor**: local clarity, consistency, or reporting issue that does not change the main conclusion.
- **Needs verification**: cannot be resolved from supplied material.

For each finding, report: location, issue, why it matters, evidence basis, and recommended action. Do not silently repair scientific content.

## Handoff

After scientific issues are resolved and the manuscript is substantively frozen, use `journal-adaptation` for target-journal formatting and compliance. After journal adaptation, a lightweight final audit may be run to ensure that formatting changes did not alter scientific meaning or internal consistency.

## Autonomous completion rule

When the user authorizes a workflow, execute the skill's complete authorized scope through its defined completion gate without waiting for a separate confirmation at every intermediate step. Continue deterministic processing, QC, record updates, figure/document preparation, and reproducibility packaging until the skill's work is complete. Ask the user only when a genuinely consequential scientific judgment could change the conclusion, indispensable information or access is missing, an irreversible/destructive or external action requires authorization, or a critical error cannot be safely resolved. Do not ask merely because another defined step remains.

For long-running calculations or retrievals, verify that the job started, record its command/configuration, output path, checkpoint, and expected duration, set a lightweight completion/failure monitor when available, and continue independent authorized work while it runs. Notify the user only for completion, failure, unexpected stop, or a required decision. Never claim completion from elapsed time alone; verify the final files and logs.

