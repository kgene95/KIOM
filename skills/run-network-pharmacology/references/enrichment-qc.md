# Enrichment QC

Apply this reference after each GO/KEGG/Reactome enrichment run and before mechanism interpretation, figure production, or docking-candidate selection.

Record the exact input branch, submitted and mapped gene counts, organism, service/package, database release, query/access date, background/universe definition, domain scope when the service exposes one, multiple-testing method, significance threshold, term identifiers, adjusted P/FDR values, GeneRatio or equivalent denominator, counts, and member genes. Preserve the raw response/export.

Run `scripts/enrichment_qc.py` on the frozen enrichment table. Treat its PASS as structural QC only. Independently review whether many displayed terms are driven by the same small gene subset, whether synonymous/parent-child terms create semantic redundancy, whether the selected background matches the analysis question, and whether any result depends on an undocumented default. Do not infer activation, inhibition, directionality, or target engagement from enrichment.

For publication figures, select terms only from the frozen enrichment rows under a recorded rule. Never replace or recalculate a displayed FDR/GeneRatio value to improve appearance. If a service does not expose the database release or background explicitly, record `not reported by source` or the actual default documented for that run rather than guessing.
