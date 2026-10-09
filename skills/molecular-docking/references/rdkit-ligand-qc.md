# RDKit-assisted ligand QC

Use RDKit as a deterministic chemistry-QC layer when it is available. It supplements, but does not replace, source-identity review, protonation decisions, ligand parameterization, or docking validation.

For each ligand, preserve the original structure and record RDKit version. Check canonical/isomeric SMILES, InChIKey when resolvable, valence/sanitization, aromaticity perception, fragments/salts, formal charge, undefined stereocenters, and atom count/order. Compare the resulting identity against the upstream NP compound record and the structure submitted to Vina.

If generating 3D coordinates, record the conformer-generation method and random seed, then minimize with a documented force field only as structure preparation. Do not interpret RDKit conformer energy as docking affinity.

Use descriptor checks such as molecular weight, H-bond donors/acceptors, rotatable bonds or TPSA only as descriptive QC or prespecified candidate filtering. PAINS or rule-of-five alerts do not invalidate a natural product automatically and must not be treated as efficacy evidence.

A tautomer/protomer/stereoisomer change creates a distinct prepared state. Record it explicitly; never silently replace the user's intended ligand with a more convenient state.
