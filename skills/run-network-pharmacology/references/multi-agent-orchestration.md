# NP multi-agent orchestration (v1, 2026-10-10)

## Purpose
This design implements a *single controlled workflow* with role-specific workers. It does not imply autonomous ChatGPT subagents or background LLM execution. Workers may be scripts, connected tools or authorized assistants. Use this design for future compounds/extracts and diseases.

## Intake by overall controller (agent 0)
Required: compound name or PubChem CID for each compound; disease name. Optional: SMILES, InChIKey, SDF, MOL2, extract-to-compound table, species (default Homo sapiens), disease ontology ID, study aim, output workspace.
Create a dedicated RUN_ID and a frozen `request.json` under `runs/<RUN_ID>/`. Resolve disease ontology and PubChem identity. Check stereochemistry, 3D conformer validity, tautomers/salts, and source-specific formats.
If chemical identity is ambiguous, request user confirmation before submissions.
Audit authorized workspace for pre-existing SEA/PharmMapper and other outputs. Show evidence matches and mismatches and obtain explicit user decision REUSE_VERIFIED or RECOLLECT_NEW before a new submission or before treating old material as study evidence. NEVER overwrite source files.

## Role 1 — NP analyst
- Start disease-target/source access audit and collect independent fast/accessible compound-target evidence immediately.
- Prepare separate immutable compound identity package: compound_id, CID, canonical/isomeric SMILES, InChIKey, provenance, validated SDF/MOL2 where required, chemical structures, SHA256, date, mapping warnings.
- Persist `handoff_to_agent2.json` with absolute *authorized local paths*, hashes, species, source parameters, submit approval/status and RUN_ID.
- Hand off as soon as structure validation passes, in parallel with disease and other target collection. Do not wait for Agent 2 before running independent branches.
- After Agent 2 returns verified archives, merge through HGNC/UniProt QC, overlap, STRING, Cytoscape, GO/KEGG and docking candidate recommendation (NO DOCKING EXECUTION).

## Role 2 — SEA & PharmMapper collector
- Read handoff manifest and verify checksums/identities before submission.
- SEA uses validated SMILES and the job/compound identity on its actual supported user interface/API; PharmMapper uses a supported MOL2/SDF upload and may require a recipient email or confirmation.
- **Email is a communication/notification channel, not the universal way of submitting structures to SEA or PharmMapper.** Prefer secure project-local handoff, not raw molecular attachments by email between worker roles. Send minimal email notification only when authorized; do not persist email addresses, secrets, or message contents in shareable data.
- If a service explicitly supports an email submission route, verify official instructions before use; never assume this.
- Submit one job per exact chemical identity only when new-collection approval is recorded. Persist `job_ledger.csv` with RUN_ID, CID, structure SHA, provider, job ID, URL, submission time, options, status; exclude private email addresses.
- Poll official job URL/email results through authorized connectors. Store PENDING without claiming background continuity absent scheduled automation. Preserve raw original, retrieval time, SHA256, source version, native ranks.
- Verify result job corresponds to submitted structure and species; fail closed as UNVERIFIED if correspondence cannot be proven. Never reuse an old job merely because its ID or name looks plausible.
- Emit `handoff_from_agent2.json` with dataset paths, result SHA256, IDs, native metrics and QC status.

## Role 3 — independent evidence auditor
- Check compound identity, source metadata, raw/processed lineage, disease universe, species, one-to-many mapping and exclusions, native-score interpretation, thresholds, STRING and enrichment mapping drift.
- Reject unverified SEA assignments from primary branch; allow explicitly labeled sensitivity/proxy branch only.
- Return PASS / CORRECT_AND_RERUN / BLOCKED_NEEDS_USER plus specific affected stages and required evidence.
- Only after independent PASS may overall controller mark COMPLETE and send final delivery.

## Overall controller orchestration
1. INTAKE -> IDENTITY_QC.
2. SOURCE_AUDIT -> WAITING_REUSE_APPROVAL if matching prior archives exist.
3. Run Role 1 independently; when valid structure package exists, queue Role 2 without requiring the entire NP analysis to finish.
4. Role 2 statuses: QUEUED, SUBMITTED, PENDING, RETRIEVED, VERIFIED, ERROR_RETRY, NEEDS_USER, UNAVAILABLE.
5. On Role 2 VERIFIED, wake Role 1 for gene mapping/merge and invalidate/rerun affected downstream branches; Role 3 re-audits.
6. Terminal status COMPLETE only after QC PASS, figures/report/manifest exist. NO docking execution.

## Fault and resource policy
- Local Python scheduler polls pending work every 30 minutes without LLM calls, respecting providers' terms/rate limits; ChatGPT checks at 09:00 and 18:00 Korea time only for meaningful changes.
- Retry transient network errors up to 3 times with bounded backoff, record alternative routes; auth/CAPTCHA/user reuse approval stops at NEEDS_USER.
- Use one reviewed Python controller invocation for multiple deterministic subtasks and durable atomic checkpoints. Do not try to bypass tool permission requests.
- Do not send raw research materials to a third-party email address without explicit authorization. Institutional privacy policies and terms of the destination service still apply.
- Gmail recipient and OAuth credentials stay runtime-private. `email_notification_status` can be logged, not addresses/message bodies.
- The GitHub repository carries reusable code/templates only; never publish research source archives, private emails, or user-specific local state.

## Required machine-readable run artifacts
`request.json`, `compound_identity.csv`, `structure_manifest.json`, `handoff_to_agent2.json`, `job_ledger.csv`, `handoff_from_agent2.json`, `source_attempts.csv`, `source_archive_index.csv`, `data_lineage.csv`, `execution_state.json`, `NP_manifest.json`, QC report and result files.

## Current project note
Previously saved SEA job folders 41debffd05f4 and 47e4702598a2 exist, with their compound assignment unverified. They are historically archived and must not be classified as verified inputs. A fresh submission can solve this, provided input compound identity and provider route are recorded. This historical example is not a universal input template.
