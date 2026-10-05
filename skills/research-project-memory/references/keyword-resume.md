# Keyword-first resume rules

Use these rules so the user can resume work with a short project/topic phrase instead of restating full context.

## Goal

Resolve short phrases such as `CMPE docking 이어서`, `멸가치 NP`, `4KIK 재검증`, or `CMPE 논문 계속` to the correct project and workflow with minimal reading.

## Resolution order

1. Parse the user's words into:
   - project alias
   - workflow alias
   - target/compound/PDB/file alias
   - resume intent such as `계속`, `이어서`, `다음`, `진행`, `재개`
2. Match project aliases against the global/project `MEMORY_INDEX.md` alias table.
3. If exactly one active project matches, resume it without asking the user to repeat background.
4. If a workflow alias is present, read only that workflow's latest checkpoint/manifest in addition to compact project state.
5. If a target, PDB, compound, figure, or manuscript keyword uniquely identifies one project in the current memory index, allow it to resolve the project even when the project name is omitted.
6. Ask a clarification only when two or more plausible active projects remain after checking aliases and current state.

## Minimal read budget

For a high-confidence keyword match, read in this order and stop as soon as enough context is recovered:

1. `AI_CONTEXT.md` or the compact summary in `PROJECT_STATE.md`
2. `NEXT_ACTIONS` and `DO NOT REPEAT`
3. relevant workflow checkpoint
4. relevant manifest
5. exact result/source file only if needed for the requested action

Do not crawl the full project tree or reread all raw files just because a project alias matched.

## Alias behavior

Maintain aliases as data, not hard-coded reasoning. Each project entry in `MEMORY_INDEX.md` should include a compact alias line such as:

```text
aliases: CMPE | 참외껍질 | Cucumis melo peel | CMPE DSS | CMPE colitis
```

When the user repeatedly uses a new unambiguous shorthand for the same project, add it to the alias list during the next meaningful checkpoint. Do not add a one-off ambiguous word as a permanent alias.

Workflow aliases may be interpreted across projects:

- `NP`, `네트워크`, `network pharmacology` -> network pharmacology
- `도킹`, `docking` -> molecular docking
- `MD`, `시뮬레이션`, `molecular dynamics` -> molecular dynamics
- `논문`, `manuscript`, `discussion`, `methods`, `results` -> manuscript workflow
- `FIG`, `figure`, `그림` -> figure/data workflow
- `IHC`, `IF`, `염색` -> wet-lab staining/interpretation context

## Seed aliases for current research workspace

Use these only as initial hints. The actual `MEMORY_INDEX.md` remains authoritative and can supersede them.

- CMPE project:
  - `CMPE`
  - `참외껍질`
  - `Cucumis melo peel`
  - `CMPE DSS`
  - `CMPE colitis`
  - uniquely-associated docking tokens may include `4KIK` when the current project index confirms the association
- MGC project:
  - `MGC`
  - `멸가치`
  - `MGC DSS`
  - `멸가치 NP`
- Achyranthis radix project:
  - `우슬`
  - `Achyranthis radix`
  - `ecdysterone` only when the current memory index confirms this project association
- AHLE project:
  - `AHLE`
  - `Adenocaulon himalaicum`

Never infer one project from a generic term such as `DSS`, `NP`, `도킹`, `논문`, `STAT3`, or `PTGS2` alone if multiple projects could contain it.

## High-confidence resume examples

- `CMPE 도킹 이어서` -> resolve CMPE + molecular docking; read compact CMPE state + docking checkpoint only.
- `멸가치 NP 다음 단계` -> resolve MGC + network pharmacology; read MGC compact state + NP checkpoint/manifest only.
- `CMPE discussion 계속` -> resolve CMPE + manuscript workflow; read compact CMPE state + latest manuscript checkpoint/draft pointers.
- `4KIK 재검증 이어서` -> resolve to CMPE docking only if the current memory index uniquely maps 4KIK there; otherwise clarify.

## Ambiguity rule

Prefer silent resolution when confidence is high and the alias maps to one active project. Do not ask the user to restate known context. Ask one short clarification only when the alias map is genuinely ambiguous or stale.
