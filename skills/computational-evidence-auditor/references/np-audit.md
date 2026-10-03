# Network pharmacology audit

## Identity and provenance

Check compound identity, canonical identifiers, stereochemistry where relevant, species, database/tool name, access date/version if available, native score meaning, and source-specific provenance. Flag silent substitutions or extract-to-single-compound simplification.

## Target and disease sets

Check stable-ID normalization, duplicate handling, aliases, one-to-many mappings, unmapped/excluded records, and species exclusions. Confirm that the analyzed overlap is traceable to the stated source sets and branch.

## Adaptive narrowing and branches

Check whether cutoffs were prespecified or adaptively introduced. Adaptive narrowing is acceptable only when lineage, before/after counts, rule change, and reason are recorded. Flag threshold tuning used only to obtain a desired historical count or prettier network.

## PPI and hubs

Check STRING organism, score threshold, mapping counts, node/edge counts, isolate policy, and whether hub metrics were calculated from the claimed graph. Do not let degree rank alone become evidence of compound binding or causal mechanism. When multiple centrality methods exist, assess robustness rather than declaring a winner.

## Enrichment

Check analyzed gene set, mapping success, background/universe when available, multiple-testing method, adjusted P values/FDR, term IDs, member genes, and whether displayed terms are copied from frozen enrichment output. Flag raw P-value-only claims when multiplicity matters. Flag pathway narratives that exceed the member-gene evidence.

## Candidate selection

Trace each docking candidate to explicit evidence axes: compound-target support, disease overlap, PPI/topology, enrichment/pathway relevance, experimental alignment, and structural docking readiness. Flag statements that call a target a top hub when it is not a top hub in the frozen branch.

## Figures

Verify counts, labels, genes, edges, ranks, pathway values and branch identity against source tables. A visually attractive network is not evidence that the underlying data are correct.
