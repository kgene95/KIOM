# Computational evidence auditor handoff

After NP completion, prepare a compact factual handoff for independent computational audit. This handoff does not rerun NP and does not start docking.

Minimum handoff:

- `NP_manifest.json` and `NP_checkpoint.md`/`.json`;
- `analysis_method_record.csv`;
- `compound_identity.csv`;
- `source_availability.csv`;
- final `compound_targets.csv` and `disease_targets.csv`;
- `overlap_primary.csv` and `branch_registry.csv`;
- `mapping_corrections.csv`;
- `PPI_results.csv` plus the exact frozen PPI node/edge tables used for topology and figures;
- hub ranking and, when performed, `hub_robustness.csv`;
- `enrichment_results.csv` plus enrichment QC record(s);
- `narrowing_audit.csv` and any sensitivity outputs;
- `docking_candidate_handoff.csv`;
- final figure QA/specification when figures exist;
- approved NP Methods/Results/legend draft when the user requests manuscript audit.

Classify missing material as `not provided`, `not generated`, or `not applicable`; never infer it. The auditor may verify, partially verify, or mark claims unverified from the available evidence, but must not silently reconstruct missing raw data.

Keep docking status `DOCKING_NOT_STARTED`. The NP handoff should state which candidate target/ligand evidence is topology-derived, pathway-derived, experimental-alignment-derived, compound-evidence-derived, or historical-manuscript-derived so the downstream docking workflow does not mistake one evidence type for another.
