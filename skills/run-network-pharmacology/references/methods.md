# Scientific methods

## 1. Define the analysis

Resolve compound identity, constituent scope, disease ontology and synonyms, organism, analysis mode, prespecified sources, access date/release, exact query, and native score schema. For de novo work, freeze source and score meaning before retrieval; decide whether narrowing is necessary only after the QC-clean broad diagnostic. Never adapt a threshold toward a desired gene, pathway, hub, or count.

## 2. Compound identity

Record supplied and preferred names, PubChem/ChEMBL/ChEBI identifiers when available, InChIKey, stereochemistry, linkage/isomer, isomeric SMILES, structure file, and identity confidence. Match a selected structure to analytical evidence. List unresolved alternatives rather than choosing silently; continue unambiguous compounds while preserving blocked ones.

## 3. Compound-target source selection and evidence

### De novo source panel

Use the run's frozen source registry as the required attempt list for de novo analysis. Attempt every registered source that can accept the study input, including the baseline sources defined in `SKILL.md`; do not stop collecting merely because another source has already produced sufficient targets. Then decide whether each retrieved source is eligible for the broad and primary branches using current accessibility, reproducibility, exact-identity safety, species suitability, provenance preservation, raw-export availability, and scientific suitability. A source may be excluded from a primary branch when access fails, CAPTCHA/login/terms block retrieval, the input is unsupported, identity or species QC fails, provenance cannot be preserved, or another prespecified scientific/QC criterion is not met; record the attempt and exact exclusion reason in `source_availability.csv`. Additional currently verifiable resources such as SwissTargetPrediction or ChEMBL may be added to the registry when scientifically useful, but additions must be frozen and documented before overlap/network analysis.

Before retrieval, audit each compound-source pair in `source_availability.csv` with:

`compound,source,source_type,accessible,exact_identity_verified,species_available,raw_export_available,native_score_available,included_in_broad,included_in_primary,branch,exclusion_reason,access_date`

Use `source_type=target_prediction`, `integrated_association`, `measured_database`, or a documented equivalent. Confirm compound identity, current access, species, raw export, preservation of the source-native score/rank, and reproducibility before freezing the panel. Record failed and unavailable sources rather than omitting them silently.

### Admission to the main compound-target union

Include a source in the primary or broad union only when all material conditions hold:

- exact compound identity is verified, including structure, isomer/stereochemistry, and linkage when relevant;
- the target organism is human or the prespecified species;
- the raw target list and source-native score/rank can be retained;
- the query, access date/release, source record, and target provenance can be recorded; and
- gene/protein identities can be normalized safely.

Otherwise do not auto-merge the result. Record it as `unavailable`, `proxy`, `broad_exploratory`, or `historical_only`, with the reason and permitted interpretation. Collect the broad useful output from admitted sources and preserve compound, source, source record, species, target identity, native score name/value/direction, rank, query structure, and evidence class.

### Source-specific controls

- **Super-PRED:** consider it for new compounds, but verify the structure rather than the name alone. Compare PubChem CID, SMILES, InChIKey, isomer/linkage, species, raw targets, and native score/rank when available. Identity-mismatched output is excluded from the main pool; retain it only as a labeled proxy or exploratory branch when scientifically useful.
- **STITCH and similar integrated association databases:** assign `evidence_class=database_supported` and `evidence_subtype=integrated_association`; do not treat them as pure predictors or direct-binding evidence. Preserve evidence channel, combined score, species, chemical and target identity, and access date/release when available. If current mapping or raw retrieval is not reproducible, classify the source as unavailable or historical-only rather than forcing it into the main union.

### Evidence classes and score boundaries

Keep these evidence classes in separate table fields and retain a source-specific subtype when useful:

- `predicted` — for example, SwissTargetPrediction, PharmMapper, SEA, or Super-PRED;
- `database_supported` — including `integrated_association` resources such as STITCH; and
- `direct_measured` — qualifying binding or biochemical assays such as suitable ChEMBL records.

For measured evidence, retain assay ID/type, target type, organism, endpoint, relation, value, unit, conditions, and confidence. A cell functional assay is not automatically direct protein binding. Never average, directly add, or convert into one composite numeric score prediction probabilities, pharmacophore-fit scores, integrated-association scores, or measured assay values.

## 4. Disease targets

Resolve the exact ontology concept before retrieval. Preserve source, evidence type, score/rank, query, release/access date, and provenance. Keep related diseases and experimental models distinct. Keep human disease evidence separate from animal or cell validation. Do not average unlike disease-database scores.

## 5. Species, stable IDs, and mapping QC

Default to human targets unless the protocol states otherwise. Prefer HGNC approved symbols and UniProt accessions. Preserve submitted identifier, aliases, complexes, isoforms, one-to-many mappings, unmapped rows, nonhuman rows, and exclusion reason. Deduplicate only after stable-ID and species mapping.

Before and after STRING, PPI, and enrichment compare:

`submitted gene -> mapped identifier -> preferredName -> species -> expected HGNC/UniProt identity`

Do not accept identity-changing automatic mapping. Verify against authoritative identity records; correct when possible. Otherwise preserve the candidate in the ledger if scientifically relevant, exclude it from downstream PPI/enrichment, record it in `mapping_corrections.csv`, and rerun the corrected branch.

## 6. Broad-first overlap and adaptive narrowing

Create the QC-clean broad compound union and broad disease union, then calculate per-compound and union overlaps. Low prediction score alone is not a broad-pool QC exclusion; sparse prediction is not proof of inactivity.

Run diagnostic PPI and enrichment on the broad overlap. Freeze it as final if modules, enrichment, and hub rankings remain interpretable. If it is too large, saturated, or diffuse, change one rule per step:

1. source-native target thresholds;
2. independent-source convergence or strong prediction plus measured/database evidence;
3. disease-evidence strength or rank;
4. STRING confidence when network density—not target validity—is the problem.

Record every step in `narrowing_audit.csv`, retaining parent sets, gained/lost genes, PPI changes, enrichment changes, hub changes, reason, and decision.

## 7. PPI and hub analysis

Use the corrected branch gene set. Record branch, organism, STRING release/access date, network type, minimum score, additional interactors, submitted/mapped/excluded genes, nodes, edges, isolates, and raw edge/mapping responses. STRING functional associations are not necessarily physical binding.

Predefine the hub method for a frozen branch, such as Degree, MCC, or a stated consensus. Preserve numerical score when available; otherwise report rank only. A hub is branch-, network-, cutoff-, and algorithm-dependent—not an absolute biological property. When conclusions depend on more than one prespecified network threshold or hub method, compare actual scenario ranks/presence and report stable versus unstable hubs; do not collapse unlike metrics into an undocumented total score.

## 8. GO, KEGG, and Reactome

Record branch, submitted/mapped genes, organism, database/release, background or gene universe, service domain scope when exposed, statistical method, multiple-testing correction, adjusted P/FDR, GeneRatio where applicable, gene count, and member genes. Run the structural checks in `enrichment-qc.md`/`scripts/enrichment_qc.py` before final interpretation. Use only actual returned terms. Disclose when several terms are driven by the same genes. Enrichment does not establish activation, inhibition, direct binding, or target engagement.

## 9. Robustness

Create sensitivity analysis only when a key conclusion may depend on a cutoff, a candidate crosses the threshold, or robustness is requested. Change one assumption at a time and keep source-native score scales separate. Report retained/lost genes, topology changes, hub changes, and stable/unstable pathways.

## 10. Evidence integration

Integrate compound evidence, disease evidence, network topology, pathway coherence, experimental alignment, and limitations without collapsing them into an undocumented score. Produce a bounded mechanism hypothesis and state the validation still required. Use [docking-candidate-selection.md](docking-candidate-selection.md) for the final recommendation.

## 11. Reproduction mode

The publication's stated databases, species, cutoffs, ranks, STRING settings, hub method, and enrichment rule define the reproduction branch. Attempt every reported compound-target source, including Super-PRED or STITCH when stated, and record each attempt in the source-availability table. Do not add an unstated cutoff, estimate unavailable output, substitute a source to match a historical count, or silently omit a failed source. If a source or raw dataset is unavailable, record `NOT INDEPENDENTLY REPRODUCED`. Any substitute dataset is a `proxy`, even when its count resembles the paper. A current best-practice de novo source panel may be analyzed in a separate lineage; never mix it with the reproduction branch.
