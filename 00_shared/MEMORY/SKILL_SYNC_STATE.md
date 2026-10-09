# Skill Synchronization State

Canonical skill source: `GITHUB_CANONICAL` = `kgene95/KIOM/skills/`

Environment IDs:
- `WEB_MOBILE` — ChatGPT web + mobile app, tracked as one logical account-level environment
- `CODEX_LAPTOP` — notebook Codex
- `CODEX_KIOM` — KIOM/company-PC Codex

Status vocabulary:
- `synced` — exact content/hash comparison confirms match with canonical
- `outdated` — exact comparison confirms an older/different copy
- `unknown` — not inspected or insufficient evidence
- `not_installed` — verified absent

## Current status

| Skill | Canonical | Last verified edit source | WEB_MOBILE | CODEX_LAPTOP | CODEX_KIOM | Notes |
|---|---|---|---|---|---|---|
| research-project-memory | GitHub main | WEB_MOBILE / Work, 2026-10-09 | unknown | unknown | unknown | Canonical address and cross-environment memory rules remain in GitHub. Reverify installed copies before marking synced. |
| browser-research-automation | GitHub main | prior ChatGPT session -> GitHub | unknown | unknown | unknown | Existing canonical skill; not changed in 2026-10-09 scientific-skill merge. |
| biomedical-research-assistant | GitHub main | current web session -> GitHub, 2026-10-09 | unknown | unknown | unknown | Preserved current GitHub workflow and added focused literature/citation retrieval routing plus specialist statistics/review handoff. |
| run-network-pharmacology | GitHub main | current web session -> GitHub, 2026-10-09 | unknown | unknown | unknown | Preserved newer GitHub source-intake/traceability controls; added BioServices-style adapter QC, RDKit chemistry QC, and advanced enrichment boundaries. |
| molecular-docking | GitHub main | current web session -> GitHub, 2026-10-09 | unknown | unknown | unknown | Preserved current Vina/redocking workflow; added RDKit-assisted ligand QC. |
| molecular-dynamics | GitHub main | current web session -> GitHub, 2026-10-09 | unknown | unknown | unknown | Preserved GROMACS-first workflow; added trajectory-analysis/convergence QC reference. |
| computational-evidence-auditor | GitHub main | prior canonical update | unknown | unknown | unknown | Existing canonical skill retained; no new 2026-10-09 external-skill changes applied. |
| manuscript-audit | GitHub main | prior canonical update | unknown | unknown | unknown | Existing canonical skill retained; no new 2026-10-09 external-skill changes applied. |
| journal-adaptation | GitHub main | prior canonical update | unknown | unknown | unknown | Existing canonical skill retained; no new 2026-10-09 external-skill changes applied. |
| literature-review | GitHub main | current web session -> GitHub, 2026-10-09 | unknown | unknown | unknown | Newly added canonical specialist skill for reproducible multi-database reviews, screening, study-level synthesis, and PRISMA-style accounting. |
| statistical-analysis | GitHub main | current web session -> GitHub, 2026-10-09 | unknown | unknown | unknown | Newly added canonical specialist skill for biomedical inferential analysis and model selection. |
| statistical-power | GitHub main | current web session -> GitHub, 2026-10-09 | unknown | unknown | unknown | Newly added canonical specialist skill for prospective sample size, MDE, attrition, and power planning. |

## Update rules

- GitHub is the master after an edited skill is validated and committed.
- Record where the edit was actually made; never infer the source environment.
- Mark an environment `synced` only after exact content/hash comparison.
- Track ChatGPT web and mobile together as `WEB_MOBILE`; if either surface shows evidence of mismatch, downgrade the combined status until resolved.
- Synchronize only skills that differ from GitHub canonical.
- Use conflict-aware merge rather than blind overwrite when an environment has valid local-only additions.
- Compare the full skill package when practical: `SKILL.md`, `agents/openai.yaml`, `references/`, `scripts/`, `assets/`, and tests when present.
- If a local/Codex skill cannot be inspected, leave it `unknown`.
- Preserve commit/hash evidence in notes when available.
