# Execution loop and asynchronous source gate (mandatory)

This file extends the scientific Skill with an operational state machine. It does not override scientific QC.

## Controller
For every NP run, maintain `execution_state.json` with state, next_action, owner, dependency, retries, last_error, resume_condition and last_updated_utc. Update atomically after each action. Never use a manifest limitation as a substitute for creating a follow-up task.

States: INIT, SOURCE_AUDIT, SOURCE_PENDING, SOURCE_READY, ID_QC, PRIMARY_FROZEN, PPI, CYTOSCAPE, ENRICHMENT, INDEPENDENT_QC, COMPLETE, BLOCKED_NEEDS_USER.

Transient error: retry up to three times with bounded backoff; then attempt two documented alternative methods. QC failure: fix underlying data or mapping and rerun dependent stages. Authentication/CAPTCHA: explain exact user action and resume trigger. Do not mark COMPLETE unless validation passes. Keep intermediate reports distinct from final delivery.

## Email-driven collection
For a submitted SEA/PharmMapper job, store job ID, compound CID, submission fingerprint, source URL and status, but never recipient email address or message content. Check authorized Gmail for matching job completion. On arrival, retrieve raw results, archive them with SHA256, verify compound identity, then automatically unblock dependent stages. If no email arrives, use official job status or queue a future check; do not claim to keep monitoring without an actual scheduled worker/automation.

## Scientific gates
No final merging of SEA jobs without a verified job-to-compound mapping. Never interpret all background SEA rows as positive predictions. Freeze the UC disease universe, human HGNC/UniProt normalization, primary target branch, STRING and Cytoscape network before final GO/KEGG or docking recommendations. Run MCODE/cytoHubba or documented verified degree fallback, save outputs and independent QC.

## Reporting
Only ask the user for a truly external blocking action. Report current state, exact reason, retry/alternative attempts, next step and resume condition. The overall manager remains responsible for following up.


## Existing-workspace evidence reuse: mandatory user approval gate
Before submitting any new SEA, PharmMapper, SwissTargetPrediction, or other source job, search the authorized project workspace for existing source archives, including previously produced Codex/webapp outputs. Verify at least compound CID and chemical identity (structure/stereochemistry when relevant), source/provider, species, source parameters/thresholds, job ID, provenance, raw completeness, retrieval date, and SHA-256. Distinguish reused historical evidence from newly collected evidence in ledgers.

If a matching existing dataset is found, do NOT silently use it, overwrite it, or submit a replacement job. Notify the user of the candidate archive path, matching and mismatching properties, verification confidence, age, and consequences for reproducibility. Explicitly ask the user to choose: (A) reuse the verified historical data, or (B) collect a new dataset. Do not proceed past the source-selection gate until a choice is recorded. If the candidate fails verification, explain the failure and recommend new collection; never call it verified.

Reuse means reference or copy the immutable raw evidence into the new run with a distinct destination filename and recorded lineage; never replace the original. New collection also archives into a new unique filename. Log approval choice, timestamp, dataset hash, and source branch in source_attempts and the execution state; do not persist sensitive email or tokens. In the state machine, use WAITING_REUSE_APPROVAL, RESUME_ON_APPROVAL, or SOURCE_PENDING as appropriate. Waiting for user approval is a legitimate blocking gate, not an analysis failure; do not retry automatically.

## Low-token monitoring
Use a local scheduler plus lightweight Python HTTP/email checks to poll pending jobs. No model call is needed for unchanged status. Trigger AI only for newly arrived results, ambiguous identity/QC, or failures requiring scientific decisions. A local scheduler is not installed merely by adding this instruction; confirm actual installation and test separately. Avoid unnecessary high-frequency polling, and respect provider rate limits and authorization.


## Remote-command batching: default execution strategy
When Remote Desktop Commander requires approval per operation, minimize calls by writing a reviewed, deterministic Python controller once and invoking it as one terminal command per run or major stage. The controller performs sequential subtasks locally, stores durable checkpoints, SHA256 archive indexes, retry attempts, error classification and resume conditions. Do not chain unreviewed arbitrary shell commands, bypass tool authorization, alter security configuration or disable safety checks. Keep original source files immutable. Batch source audit, normalization, PPI, Cytoscape and enrichment only when their dependency gates are satisfied. If a scientific gate or user approval is missing, stop safely in a persisted WAITING state, not a false COMPLETE state. A script started once is not automatically a background monitor: test scheduler setup separately.


## Operational policy: low-cost autonomous monitoring and notification
- The Windows Task Scheduler local watchdog runs every 30 minutes for deterministic, non-LLM checks. This must not call OpenAI/ChatGPT APIs or consume model tokens merely for polling. Only trigger AI for meaningful new scientific decisions or changes requiring interpretation.
- ChatGPT condition-watch checks run at 09:00 and 18:00 Korea time, not hourly, and only notify on meaningful state changes. Gmail notification is connector-dependent and must be verified before reporting delivery. Avoid duplicate notifications, and persist delivery/decision markers in an appropriate ledger.
- Work without relying on an open chat window only within the capabilities of an actually installed and tested local scheduler. Never represent a polling watchdog as a completed end-to-end NP agent; no self-development or Gmail/ChatGPT push notifications are implied by local polling alone.
- Workspace source reuse must scan historical Codex/webapp data, preserve original immutable raw files, check CID/structure/species/parameters/job association/provenance/SHA256, then request user approval to reuse or recollect. Current project user approval for reuse exists, but provenance may remain unresolved.
- To reduce Remote Desktop Commander permission prompts, run a reviewed local Python entrypoint that batches deterministic tasks; do not bypass security approvals or run unvalidated shell strings.
- Stage gates: verified raw and job assignment -> stable human IDs -> frozen disease set/primary branch -> STRING functional PPI -> Cytoscape and degree/MCODE -> GO/KEGG -> independent QC -> bilingual final report -> docking shortlist only (never docking).
- Retries: up to 3 on transient failures, 2 documented alternatives, and then stateful BLOCKED/WAITING status. Respect source terms and rate limits. Never retry scientific QC failures blindly.
- Always write durable state and next action. A source-only integrity watchdog cannot automatically unblock missing job-submission evidence.