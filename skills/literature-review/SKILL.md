---
name: literature-review
description: Conduct reproducible biomedical and scientific literature reviews with explicit search scope, multi-database retrieval, deduplication, screening, study-level extraction, evidence synthesis, citation verification, and PRISMA-style accounting. Use for systematic, scoping, narrative, rapid, or structured evidence reviews, especially when the user asks for a review protocol, reproducible search strategy, screening flow, evidence table, research-gap synthesis, or a review that must distinguish records, reports, and studies. Do not use for a simple lookup of one or a few papers.
---

# Literature review

## Scope

Run a review as a reproducible evidence workflow rather than a list of search hits. Preserve the difference between **records** retrieved from databases, **reports** describing research, and underlying **studies**. Do not infer that a literature gap exists merely because one search returned few papers.

For a focused lookup or citation check involving only a few papers, use `biomedical-research-assistant` instead.

## Workflow

1. Freeze the review question, review type, date range, population/model, intervention/exposure, comparator when relevant, outcomes, study designs, language limits, and inclusion/exclusion criteria. Mark post hoc changes.
2. Build reproducible database-specific search strategies. Use controlled vocabulary such as MeSH when appropriate, plus free-text synonyms. Record every exact query, database, interface/API, access date, and any search limits.
3. Search the minimum set of complementary sources that gives adequate coverage. For biomedical reviews, normally include PubMed/MEDLINE and at least one complementary scholarly source when comprehensiveness matters. Add preprint or broad-index sources only when they address a known coverage need.
4. Preserve raw result exports. Normalize DOI, PMID/PMCID, title, year, author, and source identifiers before deduplication. Never deduplicate solely on fuzzy title similarity when identifiers disagree.
5. Screen in stages: title/abstract, then full text. Record one primary exclusion reason at full-text stage. Keep an audit trail so included counts reconcile from retrieval through final studies.
6. Extract study-level evidence into a structured table using prespecified fields. Separate multiple reports of the same study rather than double-counting them as independent studies.
7. Assess methodological limitations and evidence applicability at the appropriate level. Do not convert a reporting checklist into a risk-of-bias instrument unless that checklist was designed for that purpose.
8. Synthesize by research question and evidence pattern, not by producing serial paper summaries. Explain consistency, heterogeneity, model/population differences, methodological limitations, and unresolved uncertainty.
9. Verify every consequential citation against the inspected source. Distinguish bibliographic identity from claim support.
10. Produce a review report with reproducible search provenance, screening accounting, evidence table, synthesis, limitations, and unresolved gaps.

## Search and completeness controls

- Count first when the source exposes a total and the review intends comprehensive retrieval.
- Paginate deterministically and reconcile expected vs retrieved counts.
- Treat index coverage, inaccessible full text, API limits, and search failures as visible limitations.
- Do not treat a successful HTTP response or an empty result page as proof of completeness.
- Do not query every database simply because it is available; use sources that add distinct coverage.

Read [search-and-screening.md](references/search-and-screening.md) for detailed retrieval, deduplication, screening, and PRISMA-style accounting rules.

## Research-gap rule

A defensible gap requires evidence from the reviewed literature. Distinguish:

- **evidence gap**: a question/outcome/population is inadequately studied;
- **methodological gap**: studies exist but have important recurring design limitations;
- **inconsistency gap**: findings conflict and the reason is unresolved;
- **translation gap**: preclinical evidence exists but clinical/real-world evidence is limited;
- **replication gap**: a finding lacks independent replication.

Do not call “few papers found” a gap without checking search adequacy and neighboring terminology.

## Outputs

Keep these distinct:

- `search_log`: database, query, date, result count, retrieval status;
- `record_table`: one row per retrieved/deduplicated record;
- `screening_log`: inclusion/exclusion decisions and reasons;
- `study_table`: one row per underlying study, linked to all reports;
- `evidence_table`: extracted methods/outcomes/findings/limitations;
- `citation_audit`: consequential claims mapped to inspected sources;
- final narrative synthesis and PRISMA-style flow counts when applicable.

If the user requests a meta-analysis, complete the review and hand off the quantitative synthesis only after confirming that effect measures, independence, comparability, and required data are adequate.

## Scientific boundaries

A literature review cannot establish experimental causality beyond the included evidence. Label preprints, abstracts-only evidence, secondary citations, and unavailable full text explicitly. Never invent missing sample sizes, statistics, methods, or outcome data.

## External design provenance

This skill was independently designed after reviewing reusable patterns from K-Dense-AI/scientific-agent-skills `paper-lookup`, `literature-review`, and `citation-management` on 2026-10-09. Preserve local workflow requirements over upstream defaults.
