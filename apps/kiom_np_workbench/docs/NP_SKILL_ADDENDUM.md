# KIOM NP skill addendum

This project-local addendum records the execution rules learned from the KIOM
workbench run. It supplements, but does not replace, the installed
`run-network-pharmacology` skill.

## Source and provenance contract

- Keep one original export per compound/source. Never merge SwissTargetPrediction,
  SEA, PharmMapper, PubChem, or disease-source rows before source-level QC.
- Preserve the original uploaded bytes in `00_project/source_archive` and record
  `raw_sha256`, `source`, `job_id`, `job_url`, `retrieved_date`, and
  `provenance_status` in the manifest.
- Use `VERIFIED` only when the official result, source identifier, and retrieval
  metadata are available. Use `PARTIALLY_VERIFIED` when some metadata is present.
  Use `UNVERIFIED` when a file's collection route or date cannot be established.
- When URL/date/confirmation are missing, the app shows an explicit broad
  exploratory confirmation before continuing. Such a source must not be
  silently promoted to a publication-ready primary branch.

## Upload and normalization contract

- Accept CSV, TSV, and ZIP exports. Preserve the ZIP/TSV original and create a
  separate KIOM CSV copy for analysis.
- Do not infer target scores, ranks, species, or source-specific settings.
  Missing values remain missing and are reported in QC.
- Keep source-native score/rank columns, job identifiers, URLs, and evidence class.

## Analysis gate and outputs

- Before overlap, require both compound-target and disease-target branches,
  species/ID QC, and an explicit exploratory override when any source is
  `UNVERIFIED`; URL/date/confirmation-complete uploads do not need that
  additional exploratory override.
- Record the human stable-ID mapping route and unmapped/ambiguous counts.
- Generate `hub_topology_degree.csv` from the frozen STRING graph. It contains
  deterministic unique-edge degree and rank; degree is network topology, not
  proof of direct binding or mechanism.
- Enrichment output must retain term IDs, member genes, background/universe when
  supplied, raw P values, and multiple-testing-adjusted values such as FDR.

## External services

SwissTargetPrediction, SEA, and PharmMapper remain official-site/user-export
sources. Do not bypass CAPTCHA, email confirmation, queue, login, or terms. A
failure, queue, or missing result is recorded as a source status and is not
replaced with another source's targets.
