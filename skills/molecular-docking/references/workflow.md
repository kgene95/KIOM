# Workflow and resume

Stages: 0 intake/resume; 1 target audit; 2 receptor QC; 3 ligand identity; 4 environment + protocol lock; 5 preparation + native-ligand redocking; 6 docking; 7 pose/score QC; 8 interactions; 9 optional independent pose/scoring sensitivity; 10 CLOSED-job integration and audit handoff.

Stage 0: read checkpoint, manifest and only pertinent CSVs. Start a new job with manifest schema v2 and record analysis start UTC, operating system, Python, actual software versions/commands/paths, database releases/access dates, planned parameters and execution route. Confirm inputs, identity audit, prior results, versions, file existence and hashes, current capabilities. A mismatched artifact invalidates that stage and descendants; record why. Create one job per receptor; keep input ligands common but never merge grids/protocols.

Stage 4: run the environment check, choose the execution route, then freeze preparation commands, receptor/ligand inputs, grid, Vina engine/version, seeds, exhaustiveness, num_modes, energy_range and output names. A change creates a new protocol ID.

Stage 5: prepare the receptor and native ligand through recorded deterministic commands. Redock the native ligand under the frozen protocol. Validation determines whether stage 6 is allowed. No native ligand: document an alternative prospective control and label validation LIMITED/UNVALIDATED; a failed redocking is BLOCKED.

Stages 6-8: use the locked protocol, record every seed/mode and retain all results. Apply predeclared pose selection, inspect top poses beyond minimum score, and create structured interaction output when the required toolchain exists. Failure of optional ProLIF does not invalidate Vina itself, but the interaction-analysis limitation must be explicit.

Stage 9: optional GNINA/other independent support may test pose/scoring sensitivity after the Vina protocol is validated. It never rescues a failed native redocking and its score scale must remain separate.

Stage 10: read only CLOSED jobs, record analysis completion UTC, create final combined tables and the optional `auditor_handoff.json`. Previous scores are historical and never mixed with new runs. Completion authorizes a manuscript-readiness summary, not automatic prose generation; ask before drafting Methods, Results or the figure legend.

For long-running services record submission ID, timestamp, inputs, version, source/status, next poll and output hash. Keep secrets outside files and chat. Print compact QC summaries; keep logs and coordinates on disk. If stopped, checkpoint identifies the precise next action.
