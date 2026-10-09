# Installed source-skill routing

Some Codex installations provide narrow life-science source skills such as ChEMBL, PubChem, Open Targets, STRING, QuickGO, Reactome, and UniProt. Treat these as retrieval adapters, not as a complete network-pharmacology workflow.

## Division of responsibility

Use a source skill when it provides the requested endpoint and is available in the current session:

| Evidence need | Source adapter | NP responsibility that remains outside the adapter |
|---|---|---|
| Compound identity and measured activity | ChEMBL, PubChem | exact structure/isomer audit, source class, raw preservation, identity confidence |
| Target or disease association context | Open Targets | disease ontology choice, evidence interpretation, branch assignment |
| Functional PPI and enrichment retrieval | STRING | frozen gene set, species/ID QC, score settings, mapping report, branch lineage |
| GO terms and annotations | QuickGO | enrichment method, background, multiple-testing rule, term-level provenance |
| Pathway context | Reactome | primary versus supporting pathway evidence and branch separation |
| Stable protein IDs and annotations | UniProt | submitted ID, alias, species, one-to-many mapping, exclusion reason |

The adapters do not replace browser-based or authorized retrieval for SEA, PharmMapper, SwissTargetPrediction, Super-PRED, STITCH, GeneCards, OMIM, or TTD when those sources are part of the frozen registry. An unavailable adapter or endpoint is recorded as `not retrieved` with the exact reason; do not silently substitute a different source.

## Full-result rule for NP analyses

Many source skills are optimized for compact summaries and default to a small number of records. That default is suitable for orientation, not for the final NP input. For an analysis run:

1. Freeze the source registry, query, species, release/access date, and native score meaning before retrieval.
2. Request or save the complete raw response when the source supports it; paginate rather than relying on a preview or `max_items` summary.
3. Preserve the raw response and checksum in `source_archive`; create normalized analysis tables separately.
4. Record the adapter name/version, endpoint, parameters, returned count, truncation or pagination warning, and any failed page.
5. Run the normal identity, species, schema, and mapping QC before overlap, STRING, or enrichment.

Never treat a compact markdown summary, a truncated API preview, or an adapter's top-5/top-10 rows as the complete target or enrichment dataset.

## What the adapter cannot prove

An API response does not by itself prove direct binding, causal disease involvement, or biological direction. Preserve the source's evidence class and native score. Keep predicted, database-supported, measured, disease, animal/cell, and historical-manuscript evidence in separate fields and do not merge unlike evidence into an undocumented score.

## Cache and update policy

Do not edit files inside the plugin cache to “upgrade” a source skill; cached plugin files may be replaced by Codex. Put project-specific routing, provenance, and QC rules in the user-level NP skill and its manifest. Recheck source adapters when their endpoint, schema, or release changes.
