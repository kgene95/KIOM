# Advanced enrichment methods and boundaries

Use this reference when enrichment goes beyond ordinary over-representation analysis (ORA), or when publication claims depend strongly on enrichment settings.

## Choose the method from the input

- **ORA**: use for a selected gene list against a defined background/universe.
- **GSEA**: use for a ranked genome-wide or sufficiently broad ranked list; do not convert a short selected list into pseudo-GSEA.
- **ssGSEA/GSVA**: use for sample-level expression matrices when per-sample pathway scoring is scientifically relevant. These methods are not substitutes for ordinary NP enrichment from an overlap gene list.

Never select a method merely because it yields more significant pathways.

## Required provenance

Record organism, identifier namespace, pathway database/release, input gene/rank definition, background universe, ranking metric and direction when applicable, minimum/maximum gene-set sizes, permutation strategy if used, multiple-testing method, significance threshold, and software/version.

For ORA, an unspecified background is a material limitation. Prefer the tested/measured gene universe or a justified database universe rather than automatically using all human genes.

## Multiple testing and redundancy

Use adjusted p-values/FDR for inferential claims. Keep raw p-values only as supporting fields. Do not mix thresholds across GO/KEGG/Reactome without recording them.

Separate statistical significance from semantic redundancy. When many terms describe the same genes/process, retain the full table and create a secondary reduced view using a documented rule such as gene-set overlap, semantic similarity, parent-child structure, or representative-term selection. Never delete terms solely to improve the figure.

## Robustness

When a mechanism claim is important, test whether it persists across reasonable background choices, cutoffs, databases, or branch definitions. Report stable themes and unstable details separately. Do not create a composite pathway score unless it was prespecified and scientifically justified.
