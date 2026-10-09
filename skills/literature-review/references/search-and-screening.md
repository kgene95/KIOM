# Search, deduplication, screening, and review accounting

## Search design

Translate the question into concepts before composing syntax. Preserve a human-readable concept map and the exact executable query. Database syntax differs; do not paste PubMed field tags into another database without translation.

Record:

- database/platform;
- exact query;
- access date;
- date/language/study-type limits;
- result count reported by the source;
- records actually retrieved;
- pagination/cursor status;
- API/interface version when known;
- failure or rate-limit notes.

## Deduplication hierarchy

Prefer stable identifiers first: DOI, PMID, PMCID, trial ID, repository ID. Then use exact normalized title/year/first-author checks. Fuzzy matching is a review queue, not an automatic deletion rule. Retain a mapping from duplicate records to the canonical record.

## Records, reports, studies

A database hit is a **record**. A publication/preprint/conference abstract is a **report**. Multiple reports can describe one **study**. PRISMA-style accounting and evidence synthesis must not conflate these levels.

## Screening

Apply prespecified inclusion/exclusion criteria consistently. Full-text exclusions should receive a single primary reason, with secondary notes optional. Resolve uncertainty explicitly rather than silently excluding borderline studies.

## Citation and full-text integrity

An abstract may support only claims actually present there. Do not describe methods, subgroup results, or mechanistic details as verified unless the relevant text/data were inspected. When only secondary sources are available, mark the evidence level.
