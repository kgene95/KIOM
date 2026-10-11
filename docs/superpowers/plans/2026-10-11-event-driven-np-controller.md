# Event-Driven NP Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ensure completed worker artifacts reconcile into the queue, ready tasks are dispatched, failures are visible, and the controller cannot silently stop.

**Architecture:** Keep the JSON queue as the durable source of truth, add a reconciliation layer that derives task completion from verified artifacts and provider ledgers, and add a controller loop that dispatches deterministic workers while recording heartbeats and events. The existing live monitor remains a display-only view of the same state.

**Tech Stack:** Python 3 standard library, JSON/JSONL state files, unittest, PowerShell launch wrapper.

**Spec:** `KIOM/harness/NP_WORKERS.md`, `KIOM/harness/EXECUTION_LOG_SCHEMA.md`, and `KIOM/skills/run-network-pharmacology/references/event-driven-orchestration.md`.

## Global Constraints

- Never mark a provider result complete without a matching job ID, CID, raw file, and SHA-256.
- Never merge PharmMapper data across different CIDs.
- One controller owns a run; workers communicate through durable artifacts and event records.
- External CAPTCHA and provider actions remain subject to existing confirmation policy.
- A worker failure must become `FAILED` or `RETRY_WAIT`, never an unreported stop.
- Controller cycles have bounded retries and a model/token budget.

## Review Focus

- A completed provider ledger must repair a stale queue status.
- A malformed or mismatched provider artifact must remain blocked and be reported.
- Independent ready tasks must be dispatched in parallel groups without sharing a resource.
- A worker exception must update the queue, event log, and controller heartbeat.
- A controller with no ready work must remain observable and schedule the next cycle.

### Task 1: Durable reconciliation

**Files:**
- Modify: `KIOM/harness/np_harness.py`
- Test: `KIOM/harness/test_np_harness.py`

**Interfaces:**
- Add `reconcile_queue(run: Path, queue: dict) -> dict`.
- It consumes `job_ledger.json`, provider manifests, and artifact checksums.
- It produces corrected task statuses plus `reconciliation` events.

- [ ] Write failing tests for stale SEA/PharmMapper completion and CID mismatch.
- [ ] Run the focused tests and verify they fail for the missing function.
- [ ] Implement reconciliation with explicit status transitions and mismatch blocking.
- [ ] Run focused tests and then the full harness test suite.

### Task 2: Worker dispatch and failure reporting

**Files:**
- Modify: `KIOM/harness/np_harness.py`
- Create: `KIOM/harness/np_controller.py`
- Test: `KIOM/harness/test_np_controller.py`

**Interfaces:**
- Add `dispatch_ready_tasks(run: Path, queue: dict, registry: dict) -> dict`.
- Add `run_controller(run: Path, interval_seconds: int, max_cycles: int) -> None`.
- Every dispatch writes `worker_started`, `worker_completed`, or `worker_failed` events and updates heartbeat state.

- [ ] Write failing tests for ready-task dispatch, exception capture, and bounded retry.
- [ ] Verify the tests fail before implementation.
- [ ] Implement deterministic dispatch through registered worker callables.
- [ ] Verify focused and full tests pass.

### Task 3: Observable watchdog

**Files:**
- Modify: `KIOM/harness/live_monitor.ps1`
- Create: `KIOM/harness/run_controller.ps1`
- Test: `KIOM/harness/test_np_controller.py`

- [ ] Write a test for stale-heartbeat detection and next-cycle scheduling.
- [ ] Implement a PowerShell launcher that keeps the Python controller alive and logs its PID.
- [ ] Add visible `RUNNING`, `WAITING`, `RETRY_WAIT`, `FAILED`, and `BUDGET_STOP` states to the live monitor.
- [ ] Verify syntax and run all tests.

### Task 4: Run repair and verification

**Files:**
- Modify: both active `work_queue.json` files only through the controller reconciliation path.
- Test: existing run fixtures plus `KIOM/harness/test_np_harness.py`.

- [ ] Run reconciliation against both NP runs.
- [ ] Verify Naringenin and CID `75596314` have no stale external-submission gate.
- [ ] Verify CID `56776173` cannot be merged into the CID `75596314` branch.
- [ ] Record a checkpoint and commit the implementation after tests pass.
