# Ligand identity

For every ligand, record input name, canonical chosen identity, PubChem CID or source ID, InChIKey, isomeric SMILES, stereochemistry, tautomer, protomer, formal charge, glycoside linkage/isomer ambiguity and source structure with retrieval date. Compare source structure atom by atom with upstream NP identity audit, if supplied. Resolve ambiguity with the user or record a prespecified enumerated set; do not choose an arbitrary isomer.

Keep native co-crystal ligand identity and bond orders separate from test ligands. Reject malformed coordinates, missing stereochemistry where consequential, salts without a policy or incompatible valence. Generate 3D with recorded software/seed, protonation pH assumptions, minimizer/force field/parameters; retain source and prepared structures and hashes. Multiple states, if used, are separate prespecified ligands and results.
