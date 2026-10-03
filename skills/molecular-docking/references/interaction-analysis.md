# Interaction analysis

Prefer a deterministic, versioned interaction pipeline for final tables. ProLIF is suitable when the local Python environment has the required dependencies and receptor/ligand files can be loaded without chemistry loss. PLIP or a documented GUI workflow may be used as an alternative, but record tool/version and criteria.

Minimum structured fields: target, ligand, pose rank, seed, residue identifier, interaction class, geometry/distance when available, method/version and source pose file. Preserve per-pose rows before collapsing to a manuscript summary.

When multiple seeds are available, calculate an interaction-consistency summary: presence count / evaluated runs for key contacts. Do not call a residue a stable interaction if it appears only in a hand-selected pose.

If ProLIF or another tool cannot run, do not fabricate interaction fingerprints. Preserve Vina results and pose files, record `interaction_analysis_status=NOT_RUN` with reason, and route the limitation to the auditor/manuscript handoff.
