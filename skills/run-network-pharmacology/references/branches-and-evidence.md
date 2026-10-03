# Branches, narrowing, and reproduction

Register every gene set used for overlap, PPI, hub analysis, enrichment, candidate selection, or figures in `branch_registry.csv`. A branch is defined by frozen inputs and rules, not its label alone.

## Branch classes

| Class | Purpose | Permitted interpretation |
| --- | --- | --- |
| `primary` | The selected final set | Main NP results and bounded mechanism hypothesis |
| `sensitivity` | Optional one-factor perturbation of the final analysis | Robustness or instability only |
| `broad_exploratory` | QC-clean broad harvest or unselected intermediate set | Diagnostic analysis and audit provenance |
| `proxy` | Substitute source or coverage/method test | Diagnostic comparison only; never primary evidence |

Required registry fields:

`branch_id,branch_class,parent_branch,purpose,compound_rule,disease_rule,sources,cutoffs,species,mapping_state,gene_count,exact_gene_file,status,permitted_interpretation,created_utc`

Each completed branch must point to an exact gene table and match its unique included-gene count. `mapping_state` must distinguish submitted, mapped, corrected, and excluded states.

## De novo lineage

Start with one lineage rather than parallel primary/sensitivity/proxy branches:

`broad_v1 -> optional narrowed children -> final_v1`

If the QC-clean broad set is interpretable, create `final_v1` as its primary child without score narrowing. Otherwise, change one rule per child and record the edge in `narrowing_audit.csv`. Preserve rejected and superseded parents. Only the selected final branch receives class `primary`.

For every comparison report the changed assumption, compound/disease/overlap counts, mapping exclusions, gained/lost genes, PPI nodes/edges/isolates, hub changes, enrichment retained/lost, and conclusion stability. If more than one assumption changes, label the result `multi-factor exploratory` and do not attribute the effect to one rule.

## Sensitivity

Create a sensitivity branch only when a key conclusion or candidate may depend on a cutoff, a reviewer requests robustness, or threshold stability is itself an outcome. Change one assumption and keep all other inputs fixed. Sensitivity evidence does not silently replace primary evidence.

## Reproduction

Apply the source-level reproduction rules in [methods.md](methods.md). Register the published workflow as its own lineage, keep substitutes as `proxy` branches, and keep any best-practice de novo analysis in a separate lineage. Historical counts are comparators, not optimization targets; a similar target, edge, hub, or pathway count does not establish reproduction.

## Evidence boundaries

Use the evidence classes defined in [methods.md](methods.md), while keeping `human_disease`, `animal_or_cell_validation`, and `historical_manuscript` evidence separate. Preserve contradictions and missing evidence. Do not transfer a hub, pathway, score, or candidate rationale from one frozen branch to another.
