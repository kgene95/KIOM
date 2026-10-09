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
| research-project-memory | GitHub main | WEB_MOBILE / Work, 2026-10-09 | synced | unknown | unknown | Installed Work skill validated and saved (bfdc317). Missing initializer guidance corrected; unused placeholder removed. UI metadata/icon aligned with the installed copy; template and canonical-address rules verified. Other Codex installations not inspected. |
| browser-research-automation | GitHub current | current ChatGPT session -> GitHub | unknown | unknown | unknown | Newly created; installed copies not yet compared. |
| run-network-pharmacology | GitHub | unknown | unknown | unknown | unknown | Compare before synchronization. |
| molecular-docking | GitHub | unknown | unknown | unknown | unknown | Compare before synchronization. |
| computational-evidence-auditor | GitHub | unknown | unknown | unknown | unknown | Compare before synchronization. |
| manuscript-audit | GitHub | unknown | unknown | unknown | unknown | Compare before synchronization. |
| journal-adaptation | GitHub | unknown | unknown | unknown | unknown | Compare before synchronization. |
| biomedical-research-assistant | GitHub | unknown | unknown | unknown | unknown | Compare before synchronization. |

## Update rules

- GitHub is the master after an edited skill is validated and committed.
- Record where the edit was actually made; never infer the source environment.
- Mark an environment `synced` only after exact content/hash comparison.
- Track ChatGPT web and mobile together as `WEB_MOBILE`; if either surface shows evidence of mismatch, downgrade the combined status until resolved.
- Synchronize only skills that differ from GitHub canonical.
- If a local/Codex skill cannot be inspected, leave it `unknown`.
- Preserve commit/hash evidence in notes when available.
