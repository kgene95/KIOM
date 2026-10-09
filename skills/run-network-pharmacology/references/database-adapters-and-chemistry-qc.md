# Database adapters and chemistry QC

Use this reference when the NP run benefits from programmatic database access or structure-aware compound QC.

## Adapter principle

Treat API libraries such as BioServices as adapters, not as scientific authorities. Record the underlying database, endpoint/service, query, species, access date, database/tool version when available, pagination/completeness status, native identifier, and native score/rank. Preserve raw responses separately from normalized tables.

Do not label an adapter as a new independent evidence source when it is only another route to the same underlying database. Deduplicate by underlying source before counting multi-source support.

Useful adapter targets include UniProt, KEGG, ChEMBL, Reactome, QuickGO, and UniChem when their official programmatic routes are available. Fall back to direct official APIs or manual exports when an adapter is unavailable or stale.

## RDKit-assisted compound QC

Use RDKit when available for deterministic structure checks before target prediction, descriptor calculation, or docking handoff. Preserve the source structure and record the RDKit version.

Check, as relevant:

- canonical and isomeric SMILES;
- InChI/InChIKey when resolvable;
- valence/sanitization failures;
- explicit stereochemistry and undefined stereocenters;
- salt/fragment policy;
- formula, exact mass, heavy-atom count and formal charge;
- tautomer/protomer policy when it affects database matching or downstream docking;
- 2D/3D atom mapping when the same compound is passed to docking.

Descriptors or filters must not silently redefine compound identity. Lipinski/Veber/PAINS-style filters, if used, are candidate-characterization aids rather than proof of efficacy or target validity.

## Provenance rule

Every adapter-derived record must remain traceable to its underlying database record and original identifier. If the underlying source cannot be verified, mark the record `UNVERIFIED` rather than treating the adapter result as authoritative.
