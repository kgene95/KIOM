# SCI figures and handoff

Apply this reference when the user requests an SCI figure, publication figure, NP figure, Fig. 2, pre-Cytoscape review draft, submission graphic, or cross-environment handoff.

## Pre-Cytoscape visual-only draft

After NP analysis and before asking about NP Methods/Results/figure legend or docking-candidate recommendation, ask whether the user wants a pre-Cytoscape `REVIEW_DRAFT` composite. Use it to review the panel grid, graph type, styling, label density, Cytoscape node/edge mapping, and publication layout before Cytoscape rendering. Label it clearly as a visual-only draft; it is neither a Cytoscape result nor `SCI-final`.

Use only frozen data from one registered branch. Do not rerun analyses or modify raw files, source exports, normalized tables, branch files, node/edge tables, or numerical results for visualization. Do not add, remove, substitute, rescale, round into a different value, or fabricate genes, nodes, edges, counts, ranks, scores, pathways, GeneRatio, FDR, or terms to improve the composition. Display transformations such as layout coordinates, bubble area, node size, and color scale are permitted only when their mapping is recorded in `visual_spec.json` and the underlying values remain unchanged.

Select a compact enrichment-term subset only from current frozen enrichment rows. Record the category, term-selection rule, and every displayed original value in `figure_qa.csv` and `visual_spec.json`. Keep Cytoscape-ready node and edge inputs as copies or deterministic exports of the frozen PPI tables, with the branch ID and mapping/QC state recorded. When Cytoscape is actually used, prefer the reproducible cyREST route in `cytoscape-automation.md` and preserve its automation record JSON alongside the figure inputs. A reference image may guide panel proportions, typography, color roles, or spacing only; it must never supply data values or network structure.

## Data integrity

Generate quantitative panels only from frozen CSV/JSON tables. Image generation may assist a workflow-layout concept, but never create or alter genes, edges, pathways, scores, ranks, or statistics. Every panel uses one frozen branch unless it is explicitly labeled as a cross-branch comparison. Do not borrow manuscript or proxy values to fill missing data. Do not write visualization-derived values back to analytical inputs or results.

## Default eight-panel main figure

Use this sequence unless the user or journal requires another structure:

| Panel | Analysis | Include | Exclude |
| --- | --- | --- | --- |
| A | Compound–target network | compounds, compound-target edges, compound-associated targets, final compound-target count | disease targets, overlap, PPI, docking recommendation |
| B | Target acquisition and disease set | target sources, main filters, compound-set count, disease source/count, species | overlap or downstream STRING counts |
| C | Compound–disease overlap | compound count, disease count, exact overlap count, Venn/equivalent | detailed mapping narrative |
| D | Corrected PPI | actual STRING nodes/edges/isolates and truthful node encoding | invented nodes, edges, or manuscript network reuse |
| E | Hub ranking | actual metric and numerical scores; rank plot when only ranks exist | fabricated relative scores |
| F | Hub subnetwork | hubs selected in E and the exact subset of D's original edges | artificial fully connected network |
| G | Integrated GO | BP, CC, and MF as three mini dot/bubble plots in one panel | fabricated terms for an empty category |
| H | KEGG enrichment | actual pathway, GeneRatio, count, FDR/adjusted P | pathways absent from current results |

Reactome may supplement or replace KEGG when scientifically justified and labeled. Do not add a docking-candidate panel to the default NP figure. Present docking candidates in Results text or a separate table; show docking results only after a separate docking workflow has produced them.

## Two-stage production gate

Use the following order unless the user explicitly requests a different review process:

1. **Composite review (`REVIEW_DRAFT`)**: generate and provide one landscape A–H composite from frozen data. Complete all panel-level data QA, but do not export or deliver separate panel files yet.
2. **User review**: collect requested corrections to layout, labels, term selection, scaling, and styling. Corrections must not alter or invent scientific values.
3. **Approved export (`SCI-final`)**: only after explicit user approval, record the approval in `visual_spec.json`, regenerate if needed, export the individual panels, and assemble the final composite package.

Do not interpret silence, file download, or absence of correction as approval. A review composite is not `SCI-final`, even when all scientific QA checks pass.

## Files and layout

During `REVIEW_DRAFT`, provide only the one-page composite; retain the plotting source, frozen inputs, `visual_spec.json`, and `figure_qa.csv` for reproducibility. Do not create the individual deliverable files listed below.

After approval, create individual panels without panel letters, large titles, or explanatory paragraphs. Retain analytical text: axes, ticks, genes, terms, legend, counts, and statistical scales. Default filenames:

- `Fig2A_compound_target_network.svg`
- `Fig2B_target_acquisition_disease_set.svg`
- `Fig2C_overlap_venn.svg`
- `Fig2D_PPI_network.svg`
- `Fig2E_hub_gene_ranking.svg`
- `Fig2F_hub_subnetwork.svg`
- `Fig2G_GO_integrated.svg`
- `Fig2H_KEGG_enrichment.svg`

Use this landscape layout for both the review and approved composite:

- top: A | B | C
- middle: D | E | F
- bottom: G at about two-thirds width | H at about one-third width

The composite contains panel letter, short analysis name, and the panel graphic—no methods or interpretation paragraphs. Adjust widths for journal dimensions, label length, and node density rather than forcing equal panels.

Use a white background, flat vectors, restrained scientific colors, one font family/hierarchy, consistent line/legend styling, aligned panels, sufficient whitespace, and labels readable at final publication size. Avoid slide/infographic styling, glossy or 3D effects, decorative biology icons, excessive gradients/colors/cards/arrows, and long text boxes.

## Deliverables

### Composite review

Provide:

1. one-page composite review figure, preferably PNG plus an editable SVG or PDF when practical;
2. frozen plotting-input tables and plotting source;
3. `visual_spec.json` with `status: REVIEW_DRAFT`;
4. `figure_qa.csv`.

### After explicit approval

Provide when feasible:

1. eight individual editable SVG panels;
2. one-page composite SVG and PDF;
3. high-resolution composite PNG and journal-required TIFF when applicable;
4. plotting source and frozen plotting-input tables;
5. `visual_spec.json`;
6. `figure_qa.csv`;
7. verified legend facts or a technical caption for handoff; create manuscript-ready legend prose only through the writing-approval gate below.

Do not export the individual panels before approval. After approval, do not stop after producing one PNG.

## visual_spec.json

Record figure number, branch ID, exact gene-set file, panel letter, analysis name, input files, data transformation, x/y encoding, node/color/size encoding, exclusions, FDR/statistical rule, layout seed, output files, and scientific limitation. Record composite files, plotting source, QA file, and caption file at the top level.

For `REVIEW_DRAFT`, leave each panel's `output_file` absent or null and do not create separate panel files. For `SCI-final`, record `user_approval_status: APPROVED` and `user_approval_recorded_utc`, then populate every panel `output_file`.

## Panel QA

Before using either `REVIEW_DRAFT` or `SCI-final`, verify and record PASS for:

- A: compound-target count and edges match the frozen target table;
- B: sources, filters, counts, species, and branch registry agree;
- C: counts and exact overlap table agree;
- D: submitted/mapped/excluded genes, nodes, edges, and isolates agree with PPI output;
- E: genes, rank, metric, and score agree with the hub table;
- F: every node is an E hub and every edge is a subset of D's original edge table;
- G: GO category, term, FDR, count, and member genes agree with enrichment data;
- H: pathway, GeneRatio, count, FDR, and member genes agree with enrichment data.

If any required value is unverified, do not call the figure `REVIEW_DRAFT` or `SCI-final`. Run `scripts/validate_figure_package.py RUN_DIR FIGURE_DIR` on the composite review and again after approved panel export. The validator infers the stage from `visual_spec.json`.

Use these `figure_qa.csv` check identifiers for A–H respectively: `target_count_and_edges`, `sources_filters_counts_species_branch`, `overlap_counts_and_exact_set`, `ppi_mapping_nodes_edges_isolates`, `hub_genes_rank_metric_score`, `hub_nodes_and_edge_subset`, `go_terms_statistics_members`, and `pathway_ratio_statistics_members`.

## Figure legend

Place methodological detail in the legend rather than inside panels: sources, access dates, branch class, proxy limitation, filters, STRING confidence/network type, mapping exclusions, hub algorithm, enrichment background, FDR/correction, and limitations.

The final legend is part of the optional manuscript-writing package, not an automatic figure export. After the composite is approved and the final panel package passes QA, ask whether to draft the NP Methods, NP Results, and figure legend. Draft the legend only after approval, using the final panel order and frozen `visual_spec.json`/QA records. A short technical caption may remain in the reproducibility handoff, but do not treat it as user-approved manuscript prose.

## Cross-environment handoff

When requested, include a concise handoff summary; canonical raw/processed/final files; branch registry; job ledger; mapping corrections; narrowing audit; checkpoint; manifest/checksums; deterministic scripts; and docking-candidate table after NP completion. Include an inventory with `file,category,role,branch,required_for_next_step,sha256`. When independent computational audit is requested, also include the minimum evidence set defined in `auditor-handoff.md`; do not recreate missing files for the audit.

Exclude credentials, recipient emails, tokens, browser state, caches, unrelated manuscript assets, redundant QA renders, and reproducible oversized files. List intentional exclusions and verify archive integrity. Distinguish confirmed, proxy, historical-manuscript, unavailable, and not-independently-reproduced evidence; state that docking has not started.
