---
name: journal-adaptation
description: Adapt a substantively finalized scientific or biomedical manuscript to a specific target journal using the journal's current official author instructions. Use when the user has chosen a journal and wants journal-specific title, abstract, section order, length, references, figures/tables, supplements, highlights, graphical abstract, declarations, cover letter, or submission-compliance changes. Do not use to decide scientific validity or to invent missing study details.
---
# Journal adaptation
## Start here: lightweight start, model escalation, and execution handoff

- Start the workflow in ordinary Chat or a fast/lower-cost model unless the user has already chosen a stronger reasoning model. Early intake, file inventory, metadata checks, deterministic extraction, routine formatting, scripted calculations, and straightforward QC usually do not justify a model upgrade.
- At the beginning of the run, tell the user once that the workflow can start in the current/lightweight model and that the Skill will explicitly recommend a stronger reasoning model when a listed scientific judgment checkpoint is reached. Do not repeatedly announce this during routine steps.
- At a listed checkpoint, briefly tell the user **before finalizing the consequential decision** that a stronger reasoning model is recommended and state the reason in one line. If the current model is already at an appropriate higher-reasoning level, continue without a redundant upgrade prompt.
- After the judgment is resolved, return routine deterministic work to the faster/lower-cost model when practical. Never rerun completed calculations, mutate a frozen branch, or change inputs merely because the model changed.

### Model-escalation checkpoints for this Skill

Recommend stronger reasoning at these points:

- interpreting journal-scope fit when the fit is not obvious from the official scope statement.
- cutting or restructuring scientific content to meet length limits when meaning or evidentiary balance could change.
- resolving conflicts between journal structure requirements and the manuscript scientific logic.
- selecting the central scientific message for highlights, graphical abstract, novelty statement, or cover letter.
- adjusting claim strength when journal-facing wording could overstate or understate the underlying evidence.

### Codex / MCP / terminal execution rules

- Maintain a **single-controller rule** for the same local PC, terminal, GUI application, project folder, or output files. Do not let Codex and MCP/Remote Desktop/another terminal automation manipulate the same resource concurrently.
- Before handing control of the same local resource to MCP, Remote Desktop, or another terminal controller, pause or disconnect Codex unless Codex itself is the sole controller executing that step. Save a checkpoint first.
- After launching a long-running external program or calculation, verify that it actually started and record the PID/job ID when available, log path, output path, command/config, and resume checkpoint.
- Recommend disconnecting/closing Codex while the external program runs **only after confirming the process is independent of the Codex session** and no active reasoning is required. Do not keep Codex connected merely to watch a GUI or wait for a calculation.
- If the calculation is a foreground or session-dependent process, **do not close Codex** because doing so may terminate the job. First detach it safely with a documented method or keep the controlling session open.
- When the external calculation or GUI step finishes, reconnect Codex only when needed for result parsing, QC, scientific interpretation, or the next deterministic command, and resume from the saved checkpoint rather than restarting the workflow.

## Workflow

1. Confirm the target journal and article type from the manuscript or user request.
2. Retrieve the current official Instructions for Authors / Author Guidelines and relevant submission pages. Prefer official publisher or journal sources over secondary summaries.
3. Extract the current requirements using `references/journal-requirements.md`.
4. Compare the manuscript with those requirements and produce a gap list before substantial restructuring when the changes are material.
5. Apply requested changes while preserving claims, numbers, citations, groups, figures, and scientific interpretation unless the user separately requests scientific revision.
6. Recheck compliance after adaptation.

## Rules

- Do not hard-code journal word limits or formatting rules in the skill; verify them at use time because policies change.
- Do not alter scientific meaning merely to fit a journal style.
- Do not invent missing ethics, author, funding, conflict, registration, data-availability, or methods information.
- If shortening is required, prioritize removing redundancy and compressing background before deleting essential methods, limitations, or qualifying language.
- If a required item is absent, flag it as missing or needs verification rather than fabricating it.
- Preserve citation identity when converting reference style.

## Output

Default to three parts:
1. **Verified journal requirements** with source links/citations.
2. **Gap analysis** showing compliant, change needed, missing, or needs verification.
3. **Adapted manuscript or exact change set** when requested.

Use `manuscript-audit` instead when the user's main need is scientific integrity, hypothesis adequacy, reporting-guideline review, or whole-manuscript evidence consistency.
