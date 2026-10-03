# Docking-candidate selection

Recommend docking targets only after the final NP branch is frozen. Integrate three evidence axes:

1. NP evidence;
2. experimental efficacy or mechanism evidence;
3. structural docking feasibility.

When supplied, inspect manuscript drafts, presentations, Prism graphs, animal efficacy, cell assays, WB, qPCR, ELISA, IHC, IF, apoptosis, and pathway-validation data. Preserve the provenance and limitations of each experimental claim.

## Candidate tiers

| Tier | Definition |
| --- | --- |
| Tier 1 — NP + experimental concordance | Compound-target and disease/network/pathway evidence align with direct animal, cell, or biochemical validation |
| Tier 2 — NP-driven candidate | Strong final-branch overlap, topology, or pathway evidence with limited direct experimental validation |
| Tier 3 — Experimental/mechanistic candidate outside final hub set | Compound evidence and strong experimental/mechanistic relevance, but possibly absent from final overlap or hub set; state this explicitly |

Tier is not rank by itself. A target outside the final overlap may be a useful mechanistic secondary candidate but cannot be described as a final-overlap or hub-derived target.

## Required assessment fields

Use these columns in `docking_candidate_handoff.csv`:

`target,ligand,compound_target_evidence,compound_target_provenance,disease_overlap,supporting_branch,hub_or_centrality,pathway_evidence,animal_validation,cell_validation,direct_biochemical_evidence,pdb_structural_suitability,binding_pocket_suitability,known_ligand_or_cocrystal_control,key_limitation,candidate_tier,recommendation_class,selection_basis,gpt_assessment,docking_status`

Allowed nonexclusive `selection_basis` values:

- `topology_derived`
- `pathway_derived`
- `compound_evidence_derived`
- `experimental_alignment`
- `historical_manuscript`

Allowed `recommendation_class` values:

- `Primary recommendation`
- `Alternative`
- `Mechanistic secondary candidate`
- `Not recommended`

## Decision rules

- Normally narrow the final recommendation to two or three targets.
- Do not create an undocumented composite score. Show each evidence dimension separately and give a clear scientific assessment.
- A topology-derived claim requires the target to satisfy the stated hub/module rule in the same branch.
- Experimental measurement alone does not prove direct ligand binding; hub status alone does not establish docking suitability.
- Structural readiness requires a defensible receptor construct, species/domain relevance, pocket, resolution/quality assessment, and preferably a known ligand or co-crystal control.
- State when the structure is absent, the pocket is uncertain, or the measured biology does not support a direct protein-ligand mechanism.

## Handoff and hard stop

Provide exact ligand identity/structure, selected targets, supporting branch, rationale, receptor/PDB candidates if already investigated, known controls, limitations, and unresolved preparation questions. Set status `DOCKING_NOT_STARTED`. Do not submit a docking job, prepare receptors/ligands for scoring, calculate poses, or interpret binding in this Skill.
