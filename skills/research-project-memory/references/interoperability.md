# Interoperability and handoff rules

## General ChatGPT chat
Use for discussion, interpretation, planning, writing, and lightweight analysis. Before continuing prior work, load the compact project state rather than relying on chat recall alone.

## ChatGPT Work
Use for multi-step browsing, connected-app work, file-heavy workflows, and longer executions. At completion, write back the resulting project state/checkpoint if write access exists; otherwise emit a handoff bundle.

## Codex
Use for repository work, deterministic scripts, terminal-oriented processing, reproducible analysis, and file transformations. Read `AI_CONTEXT.md` or `PROJECT_STATE.md` before editing. Update checkpoints and manifests after meaningful changes.

## Terminal / local computer
Treat the local environment as execution state, not project memory. Record environment name, versions, scripts, inputs, outputs, and reproducibility-critical commands in project files.

## Another GPT account
Assume account memory and private conversation history are unavailable. Transfer `AI_CONTEXT.md` plus relevant manifests/checkpoints and exact repository/cloud paths. Do not require the second account to rediscover prior decisions from raw data.

## Another AI system
Assume no hidden compatibility. Use plain Markdown/JSON/CSV/PDF/PDB/SDF and stable paths. Avoid ChatGPT-only object IDs when a portable filename or repository path exists.

## GitHub / version control
Preferred for:
- project state
- decisions
- methods
- manifests
- scripts
- compact checkpoints
- changelog

Use version history for auditability. Avoid committing credentials or very large binary raw data unless the repository is intentionally configured for them.

## OneDrive / cloud file storage
Preferred for:
- raw images
- TIFF
- PPTX
- ZIP archives
- large CSV/TSV/JSON bundles
- PDB/SDF trajectory or simulation outputs
- other large binaries

Keep stable project-relative paths in `MEMORY_INDEX.md` or `PROJECT_STATE.md`.

## Conflict resolution
If two environments changed the same research decision:
1. compare timestamps and source evidence;
2. identify whether one is a superseding decision or an accidental divergence;
3. preserve both in `DECISIONS.md`;
4. mark the active decision explicitly;
5. update `PROJECT_STATE.md` only after resolving the conflict.
