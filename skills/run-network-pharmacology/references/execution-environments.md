# Execution environments

| Work | Preferred environment |
| --- | --- |
| Current web/database/API retrieval, authenticated browsing, predictor submission, login/CAPTCHA/terms, job status and raw download | External/connected environment |
| CSV/TSV/JSON/SDF processing, normalization, deduplication, overlap, branch/audit tables, sensitivity matrices, manifests, checksums and validation | Local deterministic scripts |
| Cytoscape PPI import/layout/style/export when Cytoscape is running locally | cyREST automation from local terminal/Python |
| Chemical ambiguity, source conflict, mapping anomaly, adaptive-narrowing decision, biological interpretation, manuscript comparison and final audit | Scientific reasoning |

Use the available authorized tool that best matches the work; do not tie the Skill to a model name or platform version. Inspect runtimes before execution. Prefer installed or standard-library tooling; justify any new package before installation.

## External jobs

Immediately record service, URL, job ID, compound, exact input or checksum, organism, submission time, conformer and parameters, status, last check, retrieval route, retry, and failure reason. Use `PENDING`, `FAILED`, or `COMPLETED`. Keep retries and conformers as separate ledger rows. Do not fabricate missing timestamps or imply monitoring without a successfully configured mechanism.

Continue independent work while a job waits. Poll at the service's recommended interval or use an authorized completion notification. Validate the official output before integration.

## Deterministic and recoverable execution

Reuse raw files and completed jobs. Prefer scripts for operations that must reproduce exactly; use direct reasoning for small interpretive tasks. Keep `raw -> processed -> final` organization, avoid loading large tables into language-model context, and preserve parameters, versions, seeds, hashes, and output checksums. Checkpoint after each consequential state change according to [output-contract.md](output-contract.md).

## Local Cytoscape route

When a desktop or company PC permits local executables but GUI inspection/control is unavailable, run `scripts/environment_check.py`. A reachable local cyREST endpoint is sufficient for reproducible Cytoscape automation; direct visual control of the application window is not required. Use `scripts/cytoscape_ppi.py` only with frozen node/edge tables. If Cytoscape or cyREST is blocked, fall back to Cytoscape-ready exports plus clearly named code-based graph analysis.
