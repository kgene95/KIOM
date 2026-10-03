# Native-ligand gate

Extract native ligand from the selected structure while preserving deposited coordinates as reference. Prepare a separate dockable copy under the locked protocol. Redock blind to the deposited pose within the justified binding-site grid. Compare corresponding heavy atoms in the SAME coordinate frame; never best-fit superpose the docked ligand to the reference.

Use a validated conversion route to obtain chemically mapped coordinates for RMSD. Account for chemical symmetry/equivalent atom mappings; verify bond orders and atom mapping. State whether RMSD is top-scoring pose or best of all modes; never silently report best-of-modes as top-scoring. Record score, pose rank, seed, grid, reference/output hashes, conversion command and RMSD method.

Default top-ranked heavy-atom RMSD <=2.0 angstrom PASS; >2.0-2.5 angstrom BORDERLINE requiring documented scientific review; >2.5 angstrom FAIL. An alternative receptor-specific threshold requires prospective written rationale. A FAIL blocks test-ligand docking. Review chain, grid, native ligand assignment, protonation, waters, cofactors, receptor preparation, missing atoms and pose mapping; assign a new protocol ID and repeat redocking.

No co-crystal ligand means NATIVE_UNAVAILABLE, not PASS. Define and label an alternate validation strategy and limitation before exploratory docking.
