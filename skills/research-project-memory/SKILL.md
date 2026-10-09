---
name: research-project-memory
description: Maintain and synchronize a compact, portable research-project memory across ChatGPT chats, Work, Codex, terminal workflows, other GPT accounts, other AI systems, GitHub, and the canonical UST shared workspace. Use when the user asks to continue prior research work, recall previous decisions/results/files, hand off work between environments or accounts, avoid repeating completed analyses, create/update project checkpoints, or prepare a context package for another AI. Also use as a shared context layer before and after multi-skill research workflows such as literature review, network pharmacology, docking, MD, figure preparation, manuscript writing, manuscript review, or paper reproduction.
---

# Research Project Memory and Sync

Use this skill as the unified **cross-environment project context + synchronization layer**. It replaces the former `research-project-context-sync` role; do not maintain a separate sync skill for the same workspace.

## Canonical workspace

Read `references/workspace-locations.md` before any persistent project-memory read/write or handoff.

The canonical cross-account workspace is:

- GitHub: `kgene95/KIOM`
- UST OneDrive owner: `chskim@office.ust.ac.kr`
- UST shared-folder URL: `https://o365ust-my.sharepoint.com/:f:/g/personal/chskim_office_ust_ac_kr/IgBVWdt-alSnSJwTACfivQyMAY-UWjaYqOdCoDwDMUASmjU?e=fpGsdu`
- OneDrive workspace root: `LG_노트북/`
- Access mode: use the shared-folder URL; do not assume a direct UST OneDrive connector is available

Do not treat another connected OneDrive as the canonical workspace. The UST workspace is accessed by its shared-folder URL because direct UST connector access may be unavailable. Verify the destination before any OneDrive/SharePoint access. The OneDrive account `kgene95@gmail.com` is explicitly prohibited for this skill: do not search, list, read, write, upload, move, rename, or otherwise access that drive for research-memory or project-sync work. Never create a substitute `LG_노트북` folder on the wrong account.

## Core principles

1. Keep authoritative research state in portable text files, not only in chat history.
2. Treat Git/version-controlled project notes as the preferred source of truth for project state and decisions when available.
3. Treat OneDrive/Drive/other file storage as the preferred home for large raw files and binary outputs when available.
4. Treat conversation memory and session summaries as secondary context, never as stronger evidence than project files or raw outputs.
5. Load only the minimum relevant context needed for the current task.
6. Never repeat a completed analysis unless a documented reason exists: changed input, changed method, validation failure, new hypothesis, or explicit user request.
7. Never claim a file, repository, cloud location, or memory was updated unless the write action was actually completed and confirmed.
8. Preserve provenance: distinguish measured data, computed outputs, user decisions, AI recommendations, and unresolved hypotheses.

## Unified synchronization role

This skill owns both project-memory continuity and cross-environment synchronization. Read `references/sync-protocol.md` whenever files, checkpoints, or project state move between GitHub, the UST shared workspace, local terminal folders, Codex, Work, another GPT account, or another AI system.

Do not create a second independent memory/sync control plane. Domain skills such as network pharmacology, docking, MD, manuscript writing, figure preparation, and audit workflows keep their own manifests and scientific outputs; this skill coordinates their state and handoff.

## Keyword-first resume

Read `references/keyword-resume.md` whenever the user gives a short project/topic phrase, asks to continue prior work, or names only a project/workflow/target keyword. Resolve high-confidence aliases without asking the user to restate background. Start from the compact project context and relevant workflow checkpoint only; do not crawl the full repository by default.

Treat `MEMORY_INDEX.md` as the authoritative alias map. Maintain project aliases there so common shorthand can resume work across accounts and AI systems. Add a new alias only when repeated usage or explicit user wording makes the mapping unambiguous.

If one active project matches, continue directly. If multiple active projects still match after alias and checkpoint lookup, ask one short clarification.

## Memory lifecycle

Follow this sequence whenever project continuity matters.

### 1. Resolve the project

Identify the active project from the current request, attached files, repository path, manifest, project-state file, or user wording.

If multiple projects are plausible, prefer the project explicitly named in the current request. Do not merge similarly named projects or compounds without evidence.

### 2. Recall before acting

Before running another research skill or analysis, retrieve the smallest set of context that answers:

- What is the project question?
- What data and analyses already exist?
- What has been validated?
- What decisions are frozen?
- What must not be repeated?
- What files are authoritative?
- What is the current next action?

Prefer this order of evidence:

1. Current user instruction
2. Current raw data / primary output / manifest
3. `PROJECT_STATE.md`
4. `DECISIONS.md`
5. method-specific checkpoint or manifest
6. `HANDOFF.md` / `AI_CONTEXT.md`
7. session summaries
8. remembered conversation context

If sources conflict, do not silently choose one. Record the conflict and prefer the newest authoritative file or current explicit user instruction.

### 3. Work through the appropriate specialist skill

This skill coordinates context; it does not replace domain-specific workflows.

Examples include:

- literature and biomedical research
- network pharmacology
- molecular docking
- molecular dynamics
- figure/data preparation
- manuscript drafting
- manuscript global review
- journal-style conversion
- paper reproduction / benchmarking

Pass only relevant remembered context into the specialist workflow. Do not dump the entire project history into every task.

### 4. Checkpoint after meaningful work

After a meaningful state change, update the project memory.

Meaningful changes include:

- analysis completed or invalidated
- input set changed
- target/compound/PDB/cutoff selected
- result interpretation accepted or rejected
- manuscript claim changed
- figure set frozen
- new file generated
- next step changed
- reproducibility or QC issue discovered

Do not create a checkpoint for trivial chat or wording-only discussion unless it changes a research decision.

### Automatic-save policy

Use three persistence levels.

**Auto-save without asking** when the destination is already verified and a meaningful state change occurs, including:

- analysis or validation stage completed;
- important research decision accepted, rejected, or superseded;
- authoritative file created or materially revised;
- next action or `DO NOT REPEAT` state changed;
- reproducibility-critical error and fix established;
- method manifest/checkpoint changed.

Auto-save means update only the compact project state, decisions, manifest/checkpoint, changelog, or file-location map needed to preserve continuity. Do not upload every intermediate artifact.

**Ask before saving** when the material is substantial but provisional, including:

- exploratory hypotheses or candidate mechanisms;
- competing project strategies;
- provisional figure styles/layouts;
- large analysis packages whose canonical status is unclear;
- a change that would alter a frozen conclusion or replace an authoritative file.

**Do not persist by default**:

- casual conversation;
- one-off explanations;
- duplicated information already captured;
- long raw terminal logs;
- reproducible temporary/intermediate files;
- unsupported speculation.

If OneDrive identity cannot be verified, never auto-save there. Prefer verified GitHub state updates or prepare a handoff artifact for later upload.

### Scheduled consolidation reports

Use `references/daily-reporting.md` when a scheduled or on-demand work report is requested.

- Do not require the user to update memory in every conversation manually.
- Preserve meaningful changes at the time they occur through normal checkpoints.
- Use scheduled reports as a second layer that consolidates already-persisted project state; do not rely on the report job to rediscover every prior chat.
- Default scheduled cadence for this workspace is 08:00 and 15:00 local time when the user has enabled the automation.
- At each run, read only the compact memory/index/checkpoint files and repository changes since the previous report, then summarize completed work, important decisions, created/modified files, blocked items, `DO NOT REPEAT`, and next actions.
- Save a dated report under the canonical GitHub memory area when write access is available, and update the shared activity/current-work index only when state changed.
- If a relevant change exists only inside an inaccessible chat, attachment, or local environment, mark it as a memory gap instead of fabricating or silently omitting provenance.

### 5. Prepare handoff when switching environments

When moving between ChatGPT chat, Work, Codex, terminal, another GPT account, or another AI system, create/update a compact handoff bundle.

The minimum handoff should contain:

- `AI_CONTEXT.md`
- `PROJECT_STATE.md`
- `DECISIONS.md`
- `NEXT_ACTIONS` section within `PROJECT_STATE.md`
- relevant method manifests/checkpoints
- file-location map

Do not require the receiving AI to reread the entire repository or every raw file.

## Required memory files

Use the schemas in `references/memory-schema.md`.

Preferred project structure:

```text
00_PROJECT/
├── MEMORY_INDEX.md
├── PROJECT_STATE.md
├── DECISIONS.md
├── AI_CONTEXT.md
├── HANDOFF.md
└── sessions/
    └── YYYY-MM-DD_<topic>.md
```

Method-specific manifests/checkpoints stay near their own workflow outputs, for example:

```text
NP_manifest.json
network_pharmacology_checkpoint.md
docking_manifest.json
docking_checkpoint.md
md_manifest.json
md_checkpoint.md
```

Do not duplicate full method results inside memory files. Store summaries and paths/identifiers.

## Compact context rule

When resuming a project, reconstruct context in this order:

1. one-paragraph project objective
2. current evidence status
3. frozen decisions
4. open issues
5. next recommended action
6. exact paths/IDs of files needed for the next step

Default target: a compact brief that another capable model can understand without reopening all previous conversations.

## Decision logging

For every nontrivial research decision, record:

- date
- decision
- status: `accepted`, `provisional`, `rejected`, or `superseded`
- scientific rationale
- evidence/files used
- what this decision changes
- supersedes / superseded-by relation if applicable

Never rewrite history by deleting an old decision when a new decision replaces it. Mark the old decision as superseded.

## Handoff rules by environment

Read `references/interoperability.md` when work moves between environments, accounts, or AI systems.

Key rule: assume no environment shares hidden context unless an accessible file, connector, repository, or explicit handoff artifact confirms it.

## Research integrity rules

- Separate experimental evidence from computational prediction.
- Separate pre-specified hypotheses from post hoc interpretation.
- Do not promote docking, network pharmacology, MD, or enrichment results to experimentally validated mechanism without supporting evidence.
- Preserve exact species, structure IDs, thresholds, versions, database dates, sample sizes, and file provenance when these affect interpretation.
- If the current memory conflicts with raw data, raw data wins and the memory must be corrected.
- If a previous AI summary cannot be traced to a file or conversation source and it matters scientifically, treat it as unverified.

## Cross-account and cross-AI portability

When the user wants to continue work in another GPT account or another AI:

1. Create/update `AI_CONTEXT.md` using the template in `assets/templates/AI_CONTEXT.md`.
2. Include only portable facts, decisions, paths, identifiers, and next actions.
3. Exclude passwords, API keys, access tokens, personal identifiers, and connector secrets.
4. Prefer stable repository paths and filenames over chat-specific references.
5. Include a `DO NOT REPEAT` section for completed analyses.
6. Include a `VERIFY FIRST` section for unresolved or stale facts.

## Terminal-aware workflows

When terminal or Codex work is required:

- record command/script location, environment name, tool versions, and output path;
- record the machine identity as `LAPTOP` or `WORKPC` when the work is performed on one of the user's two Codex computers;
- record `environment` (for example `Codex`, `terminal`, or `Work`), `local_root`, and per-destination sync state when they are known;
- never infer the machine from a path, hostname, or prior conversation. If machine identity is not verified, use `UNKNOWN_MACHINE` and surface it as a memory gap when relevant;
- when the same workflow exists on both computers, prefer the newest authoritative validated checkpoint rather than the newest local timestamp alone;
- treat unsynchronized local outputs as machine-local state until GitHub/UST synchronization is confirmed;
- do not copy long terminal logs into project memory;
- summarize failures, fixes, and reproducibility-critical commands only;
- preserve generated manifests/checkpoints in the project structure;
- if work moves between the two computers, ensure the receiving machine can reconstruct the environment or identify missing dependencies before continuing.

## Skill provenance and synchronization

Treat GitHub `kgene95/KIOM/skills/` as the canonical master for reusable research skills unless the user explicitly changes the authority.

Track these execution environments separately:

- `WEB_MOBILE` = ChatGPT web and mobile app as one logical account-level environment
- `CODEX_LAPTOP` = notebook Codex installation
- `CODEX_KIOM` = KIOM/company-PC Codex installation
- `GITHUB_CANONICAL` = authoritative repository copy

Whenever a skill is materially edited:

1. Record the verified source environment in the shared skill-sync state.
2. Validate the edited skill before treating it as canonical.
3. Update the GitHub canonical copy.
4. Record the canonical commit/SHA when available.
5. Mark only environments that were actually compared with the canonical copy as `synced`.
6. Treat ChatGPT web and mobile as the single logical environment `WEB_MOBILE`; if either surface shows evidence of a mismatch, mark `WEB_MOBILE` as `unknown` or `outdated` until resolved.
7. Mark a verified older copy as `outdated`.
8. Compare content hashes or exact file contents when possible; do not rely only on filenames, ZIP names, timestamps, or chat memory.
9. When synchronizing, update only skills that differ from the canonical copy instead of blindly replacing every installed skill.
10. If an environment cannot be inspected, preserve that as a synchronization gap rather than claiming success.

Use `00_shared/MEMORY/SKILL_SYNC_STATE.md` as the compact cross-environment status register when available. Skill synchronization state is operational provenance, not scientific evidence.

## Memory maintenance

Periodically compact stale session logs into `PROJECT_STATE.md` and `DECISIONS.md`.

Keep session logs as provenance, but do not force every future task to load them.

Use `MEMORY_INDEX.md` as a directory of authoritative state files and major project outputs.

## Initialization

If a project has no memory structure and filesystem access is available, run:

```bash
python scripts/init_project_memory.py <project_root>
```

This creates only missing memory files and does not overwrite existing content.

If filesystem access is unavailable, generate the equivalent markdown bundle in the current environment for the user to save into the project repository.
