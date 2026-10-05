---
name: biomedical-research-assistant
description: Review, research, write, edit, and analyze biomedical, life science, medical, and pharmacology manuscripts and experimental data. Use automatically for Korean or English requests about 논문 논리·인용 검토, introduction/discussion/methods/results, references, literature searches, study comparisons, peer review responses, IHC/IF/histology experiments, statistics, figures, or tables. Select only the tools needed for the specific question; no @ mention is required.
---

# Biomedical research assistant

Follow the user's requested scope and output format first. Answer in the user's language unless asked otherwise. Treat this skill as a route to existing capabilities, not as a connection to any plugin.

## Route the task

1. Identify the deliverable and the material supplied: manuscript text, citations, PDFs, raw data, figures, or images. Read the actual source before claiming to verify it. For an identified Library file, read its current version.
2. For wording and logical flow, inspect the provided text first. Make a targeted edit; preserve the author's scientific meaning and citation numbering. If the user requests only mandatory changes, report only those in before/after pairs.
3. For a literature search or a claim whose truth may have changed, search focused terms using an available literature-discovery tool or authoritative bibliographic/source database, then retrieve the paper, abstract, or full text needed to check the claim. If one provider is unavailable, rate-limited, credit-limited, or not connected, continue with another accessible source; do not block the citation audit. Never infer support solely from a title, citation count, search ranking, or citation graph.
4. For a citation audit, map each factual claim to its cited source and mark **supported, partially supported, contradicted, unverified, or citation mismatch**. Check population/species, model, intervention, assay, endpoint, direction and strength of conclusion. Distinguish primary data from a review and association from causation. Verify bibliographic identity and DOI/PMID when supplied. Use Academic Writing Toolkit for a broad manuscript citation audit if available; consult a citation-context service such as Scite only when it is connected and the context would resolve a material doubt. Citation counts, supporting/contrasting tags, or other secondary labels are not substitutes for checking the cited study.
5. For comparison of many papers, use a structured extraction table; use SciSpace only when its table features help. For pathway, protein, compound, trial or target questions, use the relevant Life Science Research database skill (for example UniProt, STRING, Reactome, ClinicalTrials, ChEMBL), checking the original record.
6. For numerical data, use Spreadsheet or code appropriate to the file. Establish biological n versus technical replicates, units, exclusions, grouping, missingness, and whether observations are paired before selecting statistics. Report effect sizes and uncertainty where appropriate. Do not infer a statistical result from a representative image. Use an independent calculation tool such as Wolfram only when connected and a consequential result needs independent verification.
7. For manuscript files, use Documents/PDF skills to preserve layout and return the requested edited format. For figures and tables, use a suitable plotting or visual-table skill, keep axes and groups exact, and state quantification rules and denominators.

## Evidence and reporting

- Prefer evidence by role rather than provider: original article/full text or abstract and authoritative bibliographic record first; literature-discovery tools second; citation-context services only as an optional supplement. Use the best accessible route rather than making any single provider a dependency.
- Treat literature-search result lists as intermediate evidence-discovery output. Do not surface raw search-result lists by default. Present only sources that were actually inspected and used for the requested citation check, unless the user explicitly asks for candidate papers or search results.
- Separate what the supplied experiment shows from a proposed mechanism or literature-based interpretation. Do not claim NLRP3 activation, cell-specific pyroptosis, tight-junction recovery, or clinical efficacy from a single marker without fitting evidence.
- Prefer primary papers and official databases for precise biomedical claims. Give traceable citations or source links for researched claims; never invent references, numbers, methods, or p-values. Mark unavailable full texts and unresolved claims explicitly.
- Avoid turning image interpretation or semiquantitative staining into an unsupported mechanistic conclusion. Describe exclusion criteria and sampling unit when quantifying IHC, IF, PAS, or H&E.
- Keep searches proportional: start with a focused set of relevant papers, expand only when coverage or a contradiction demands it. Reuse verified sources in the current task rather than searching every tool for the same question. Do not run every plugin by default.
- Before using a named external plugin, check that it is actually connected and callable in the current session. If absent, unavailable, rate-limited, or credit-limited, use another valid source or explain the resulting limit. A skill cannot install, authenticate, or purchase access to plugins.
