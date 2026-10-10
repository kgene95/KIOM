# Generic Harness and Agent System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a domain-neutral harness and agent contract that can question, plan, isolate, execute, verify, recover, and finish research or software projects without repeatedly asking the same questions or silently stopping.

**Architecture:** The harness owns lifecycle control, state, workflow DAGs, approvals, retries, budgets, worktree coordination, notifications, and completion evidence. Agent contracts define controller, worker, reviewer, and verifier responsibilities. Domain adapters such as NP provide scientific tasks and artifact contracts without redefining the lifecycle.

**Tech Stack:** Markdown contracts, JSON schemas, Python standard-library controller, Git worktrees, Git commit/merge records, deterministic tests, optional connectors (Gmail, browser, GitHub), and model routing policy.

**Spec:** `HARNESS_GUIDE.md`, `AGENT_CONTRACT.md`, `WORKFLOW_SCHEMA.md`, `CODEX/ChatGPT.md`, and this plan.

## Global Constraints

- A workflow is a logical DAG/state machine; a worktree is an isolated filesystem/Git execution location. They must never be treated as synonyms.
- Do not claim completion without fresh verification evidence.
- Do not repeat a user question when the answer is already in a durable project state, decision log, manifest, or active approval.
- Do not run independent tasks serially when their files and resources are independent.
- Do not run parallel workers against the same files, GUI, provider account, or external job.
- A bug fix requires reproduce → failing test → minimal fix → passing test → full regression test.
- Commit, merge, and completion are separate states with explicit evidence.
- External actions, credentials, destructive changes, publication, and final scientific conclusions require the configured approval gate.
- Deterministic checks and low-risk work must not consume a high-cost model.

## Review Focus

- A task can be resumed after the chat or process ends: test by killing a run after checkpoint and resuming it.
- A failed task cannot loop forever: test bounded retries and `BUDGET_STOP`.
- A worker cannot claim success without artifacts: test missing output and invalid SHA.
- A bug fix is not accepted without a red-green regression cycle: test the original failure before and after the fix.
- A merged change remains traceable: test commit, merge target, verification report, and completion record.

---

### Task 1: Freeze the generic vocabulary and state machine

**Files:**
- Create: `HARNESS_GUIDE.md`
- Create: `WORKFLOW_SCHEMA.md`
- Create: `schemas/workflow.schema.json`
- Create: `schemas/task.schema.json`
- Test: `tests/harness/test_schema_contract.py`

**Interfaces:**
- Consumes: user goal, project state, approval policy
- Produces: states `INTAKE`, `PLANNED`, `READY`, `RUNNING`, `WAITING_USER`, `WAITING_EXTERNAL`, `FAILED_RETRYABLE`, `BLOCKED`, `INVALIDATED`, `VERIFIED`, `COMMITTED`, `MERGED`, `COMPLETE`, `BUDGET_STOP`

- [ ] Write failing schema tests for workflow/task identity, dependency, resource lock, retry budget, checkpoint, and next action.
- [ ] Run the schema tests and confirm they fail for missing required fields.
- [ ] Write the generic lifecycle and distinguish workflow, worktree, task, worker, artifact, gate, checkpoint, and completion.
- [ ] Implement JSON schemas and deterministic validation.
- [ ] Run schema tests and confirm they pass.
- [ ] Commit `docs: define generic harness vocabulary and state machine`.

### Task 2: Define the agent contract and questioning protocol

**Files:**
- Create: `AGENT_CONTRACT.md`
- Create: `CODEX/ChatGPT.md`
- Create: `AGENTS.md`
- Create: `schemas/agent_contract.schema.json`
- Test: `tests/harness/test_agent_contract.py`

**Interfaces:**
- Consumes: generic state machine from Task 1
- Produces: controller, planner, worker, reviewer, verifier, notifier roles and a durable question/decision record

- [ ] Write failing tests for question deduplication, decision persistence, explicit approval, and role output contracts.
- [ ] Run tests and confirm failure.
- [ ] Define the question protocol: ask only for missing, consequential, or irreversible decisions; load existing answers first.
- [ ] Define Codex/ChatGPT environment behavior without duplicating platform-neutral rules.
- [ ] Implement contract validation and decision lookup.
- [ ] Run tests and confirm pass.
- [ ] Commit `docs: add generic agent and Codex contracts`.

### Task 3: Add workflow planning, worktree isolation, and parallel dispatch

**Files:**
- Create: `WORKTREE_POLICY.md`
- Create: `harness/planner.py`
- Create: `harness/dispatcher.py`
- Create: `harness/worktree_manager.py`
- Test: `tests/harness/test_planner.py`
- Test: `tests/harness/test_dispatcher.py`

**Interfaces:**
- Consumes: validated workflow and agent contracts
- Produces: `plan.json`, `dispatch_plan.json`, worktree identity, resource locks, and worker assignments

- [ ] Write failing tests proving independent tasks share a parallel group while shared-resource tasks serialize.
- [ ] Write failing tests proving a worktree is attached to a task and never mistaken for a workflow.
- [ ] Implement DAG planning and resource conflict detection.
- [ ] Implement worktree lifecycle: detect existing isolation, create or reuse only an authorized worktree, record branch/ref/path, and verify baseline tests.
- [ ] Implement bounded parallel dispatch with one owner per resource.
- [ ] Run targeted and full tests.
- [ ] Commit `feat: add workflow planning and isolated dispatch`.

### Task 4: Add execution log, checkpoint, recovery, and bug-fix loop

**Files:**
- Create: `EXECUTION_LOG.md`
- Create: `RECOVERY_POLICY.md`
- Create: `harness/state_store.py`
- Create: `harness/recovery.py`
- Test: `tests/harness/test_recovery.py`

**Interfaces:**
- Consumes: task result, error class, artifact manifest
- Produces: JSONL event log, atomic state, resume condition, retry record, invalidation event

- [ ] Write a regression test that reproduces a known stop/duplicate-question symptom and confirm it fails.
- [ ] Implement the minimal state/checkpoint/recovery behavior.
- [ ] Confirm the regression test passes.
- [ ] Add retry classes, alternative route limits, timeout handling, and `BLOCKED`/`BUDGET_STOP` transitions.
- [ ] Run full regression tests and confirm no stale state is reused.
- [ ] Commit `feat: add durable recovery and regression loop`.

### Task 5: Add verification gates, provenance, and completion evidence

**Files:**
- Create: `VALIDATION_GATES.md`
- Create: `EVALUATION_GUIDE.md`
- Create: `harness/verifier.py`
- Create: `harness/completion.py`
- Test: `tests/harness/test_verification.py`

**Interfaces:**
- Consumes: artifacts, hashes, tests, reviewer verdicts, Git status
- Produces: `verification_report.json`, `completion_record.json`, PASS/REVISE/BLOCKED verdicts

- [ ] Write failing tests for absent artifact, changed input hash, failing test, unmerged commit, and missing reviewer verdict.
- [ ] Implement artifact, test, provenance, and Git evidence checks.
- [ ] Implement completion only after all required gates pass.
- [ ] Run tests and verify that elapsed time or worker claims cannot produce `COMPLETE`.
- [ ] Commit `feat: enforce evidence-based verification and completion`.

### Task 6: Add model routing, approval, connector, and notification policies

**Files:**
- Create: `APPROVAL_POLICY.md`
- Create: `MODEL_ROUTING_POLICY.md`
- Create: `CONNECTOR_POLICY.md`
- Create: `harness/policy.py`
- Test: `tests/harness/test_policy.py`

**Interfaces:**
- Consumes: task risk, model budget, connector status, user decisions
- Produces: approval request, model selection, connector event, notification event

- [ ] Write tests proving deterministic work uses no model, routine work uses a lower-cost model, and high-impact ambiguity escalates.
- [ ] Write tests proving Gmail/provider events unblock tasks only after identity and SHA checks.
- [ ] Implement approval, model routing, connector status, notification deduplication, and quiet healthy polling.
- [ ] Run policy tests and record connector availability separately from connector verification.
- [ ] Commit `feat: add policy and connector gates`.

### Task 7: Add domain adapter contract and NP adapter

**Files:**
- Create: `ADAPTER_GUIDE.md`
- Create: `adapters/np.md`
- Modify: `skills/run-network-pharmacology/SKILL.md`
- Modify: `harness/np_harness.py`
- Test: `tests/adapters/test_np_adapter.py`

**Interfaces:**
- Consumes: generic runner and contracts from Tasks 1–6
- Produces: NP task mapping, provider event mapping, scientific completion gates, and NP-specific handoff

- [ ] Write adapter tests for structure handoff, SEA/PharmMapper/Gmail events, mapping QC, independent QC, and docking stop.
- [ ] Implement NP adapter without copying generic lifecycle rules into the scientific Skill.
- [ ] Run NP adapter tests and the existing NP regression suite.
- [ ] Commit `feat: connect network pharmacology domain adapter`.

### Task 8: Integrate Git commit, merge, and completion lifecycle

**Files:**
- Create: `RELEASE_AND_MERGE_POLICY.md`
- Create: `harness/git_lifecycle.py`
- Test: `tests/harness/test_git_lifecycle.py`

**Interfaces:**
- Consumes: verified branch, worktree, test report, review result
- Produces: commit record, merge record, conflict/recovery state, completion record

- [ ] Write failing tests for dirty worktree, unverified tests, missing review, merge conflict, and successful merge.
- [ ] Implement commit-before-merge and evidence checks.
- [ ] Require conflict resolution and rerun verification after merge.
- [ ] Run full test suite, diff check, and completion audit.
- [ ] Commit `feat: add evidence-based Git lifecycle`.

## Plan self-review

This plan separates generic lifecycle from NP science, explicitly distinguishes workflow from worktree, covers parallelism, repeated questions, bug reproduction, verification, recovery, connectors, cost control, and Git completion. It leaves real connector credentials and irreversible external actions behind approval gates.
