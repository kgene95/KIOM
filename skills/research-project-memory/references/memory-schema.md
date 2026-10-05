# Memory file schemas

## MEMORY_INDEX.md
Purpose: fast navigation without rereading the project.

Required sections:
- Project name
- Canonical repository/root
- Raw-data storage root
- Authoritative state files
- Active method checkpoints/manifests
- Key result files
- Last checkpoint date
- Current active task

## PROJECT_STATE.md
Purpose: canonical compact state of the project.

Required sections:
1. Project objective
2. Current scientific question
3. Existing experimental evidence
4. Existing computational analyses
5. Validated / frozen outputs
6. Known limitations or unresolved issues
7. Do not repeat
8. Next actions, prioritized
9. Key file locations
10. Last updated

Keep this file concise. Prefer summaries plus file paths rather than embedded result tables.

## DECISIONS.md
Purpose: append-only decision ledger.

Each entry:

```markdown
## YYYY-MM-DD — <decision title>
- Status: accepted | provisional | rejected | superseded
- Decision:
- Rationale:
- Evidence:
- Consequence:
- Supersedes:
- Superseded by:
```

## AI_CONTEXT.md
Purpose: portable context for a new chat, account, agent, or AI.

Required sections:
- Project identity
- One-paragraph objective
- Current state
- Frozen decisions
- Do not repeat
- Verify first
- Next action
- File map
- Tool/environment notes

Target length: short enough to paste into another model without overwhelming context.

## HANDOFF.md
Purpose: record a specific transfer of work.

Required sections:
- From environment
- To environment
- Date
- Work completed
- Files created/modified
- Decisions made
- Open issues
- Exact next step
- Required tools/connectors

## Session log
Purpose: provenance, not primary context.

Record:
- date
- environment
- task
- actions
- important outputs
- decisions
- unresolved issues
- files touched
- suggested next step

Do not paste full chat transcripts or long terminal logs.

## Project alias index

In `MEMORY_INDEX.md`, maintain a compact `aliases:` field for each active project so short phrases can resume work across accounts. Include stable user shorthand, Korean/English project names, and only uniquely-associated target/PDB/compound tokens. Do not use generic workflow words as project aliases.
