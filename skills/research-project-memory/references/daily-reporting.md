# Daily Memory Consolidation Reports

Use this reference for scheduled or on-demand project work reports.

## Purpose

The report is a consolidation layer, not the primary memory store. Meaningful work should still be checkpointed when it happens. Scheduled reports summarize persisted state and surface gaps so another chat, account, or AI can resume with minimal rereading.

## Default cadence

When the user enables scheduling, use the user's local timezone and run at:

- 08:00
- 15:00

Do not create a schedule without explicit user opt-in.

## Inputs

Read only what is needed:

1. `MEMORY_INDEX.md`
2. active projects' `PROJECT_STATE.md`
3. relevant `DECISIONS.md`
4. method manifests/checkpoints changed since the last report
5. GitHub changes since the previous report
6. latest `HANDOFF.md` / `AI_CONTEXT.md` when needed

Do not attempt to crawl every prior chat or reload all raw files.

## Output

Use this compact structure:

```text
GPT WORK REPORT
YYYY-MM-DD HH:MM

Changed projects
- ...

Completed
- ...

Important decisions
- ...

Created / modified files
- ...

Blocked / unresolved
- ...

DO NOT REPEAT
- ...

Next actions
1. ...
2. ...

Synchronization
- GitHub: ...
- UST workspace: ...
- LAPTOP Codex/local: ...
- WORKPC Codex/local: ...
- UNKNOWN_MACHINE / unsynchronized local state: ...
- Skills: GITHUB_CANONICAL / WEB_MOBILE / CODEX_LAPTOP / CODEX_KIOM ...

Memory gaps
- ...
```

## Persistence

If GitHub write access is available, save reports under a shared memory area such as:

```text
00_shared/MEMORY/
├── ACTIVITY_LOG.md
├── CURRENT_WORK.md
└── DAILY_REPORTS/
    └── YYYY-MM-DD_HHMM.md
```

Update `ACTIVITY_LOG.md` and `CURRENT_WORK.md` only when state changed.

If no meaningful change occurred since the previous report, produce a brief no-change report and do not rewrite authoritative project state unnecessarily.

## Integrity rules

- Never claim access to a chat, attachment, local file, or workspace that was not actually accessible.
- If a change is known to exist only in an inaccessible location, list it under **Memory gaps**.
- Do not infer missing decisions or fabricate file paths.
- Preserve exact project aliases, filenames, IDs, and status labels where relevant.
- Scheduled reports never replace per-project checkpoints or manifests.
- When machine provenance is recorded, distinguish `LAPTOP` and `WORKPC` Codex/local changes instead of merging them into a generic Codex entry.
- If a Codex/local change lacks verified machine identity or synchronization evidence, report it as `UNKNOWN_MACHINE` or a memory gap rather than guessing.
- For skill changes, report the verified edit source and synchronization status across `WEB_MOBILE`, `CODEX_LAPTOP`, and `CODEX_KIOM` when that evidence exists; otherwise mark the environment `unknown`.
