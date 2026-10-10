# KIOM research workspace

This repository is the versioned control plane for the OneDrive workspace `LG_노트북/`.
OneDrive stores raw and large research files; GitHub stores skills, scripts, manifests, checkpoints, status records, and small reproducibility tables.

## Canonical projects

- `01_CMPE/CMPE_Docking/` — CMPE (참외껍질) docking package.
- `02_MGC/MGC_Docking/` — MGC package.
- `skills/` — reusable analysis skills.

Read `PROJECT_INDEX.md`, then the project's `PROJECT_README.md` or `00_PROJECT/README_AGENT.md` before continuing work. Do not rerun a completed branch when the checkpoint and hashes are current.

Large structures, trajectories, logs, PDFs, PPT files, figures, and other raw data remain in the matching OneDrive project folder. GitHub records their OneDrive path and hash when needed.

## Project and harness entrypoints

- `PROJECT.md` — project scope and storage boundary
- `HARNESS_GUIDE.md` — generic harness lifecycle
- `AGENT_CONTRACT.md` — controller, worker, reviewer, verifier contracts
- `CODEX/ChatGPT.md` — Codex/ChatGPT environment rules
- `PROJECT_STATE.md` — current status and next actions
- `00_shared/MEMORY/DECISIONS.md` — durable project decisions
- `adapters/` — domain-specific connections

## Failure-learning and harness rule

When any analysis, dashboard, source submission, retrieval, QC, or handoff fails or behaves unexpectedly, fix the root cause and update the same change set in the relevant skill, Agent 0–5 orchestration guidance, executable tool, and project checkpoint/manifest. Before declaring it repaired, search every affected instruction and state document for stale or contradictory statements about the prior behavior; delete or replace every match, then record a zero-match verification. Add or update a meaningful acceptance check that proves the repaired behavior. Do not declare the issue resolved until the updated tool passes the check and the state transition is recorded. For verified SEA and PharmMapper paths, the acceptance chain is: approved input → immutable structure SHA → official submission → job/task ID and URL → monitored raw-result retrieval → SHA/provenance QC → downstream handoff.

## NP execution harness

The reusable NP science rules remain under `skills/run-network-pharmacology/`. The durable orchestration layer is documented in `HARNESS.md`, role contracts are in `agents/AGENTS.md`, and the first safe controller is `harness/np_harness.py`. The controller records a resumable cycle, derives parallel dispatch groups, preserves approval/external waiting states, and stops at explicit cycle budgets rather than looping indefinitely.
