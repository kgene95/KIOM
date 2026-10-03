# Protocol lock and execution

Before docking, write receptor source/PDB, chain/assembly, retained unit, water and HETATM policy, native ligand treatment, metals/cofactors/heme, hydrogens, protonation/charges and missing-residue handling; ligand source, protomer/tautomer/stereochemistry, 3D generation/minimization and output format. Preserve exact software versions, executable paths, commands and preparation logs. Inspect PDBQT atom types, rotatable bonds, hydrogens/charges and coordinate frame after conversion.

Use a native binding site or independently justified pocket. Record grid center x/y/z and size x/y/z in angstrom, scoring function, exhaustiveness, num_modes, energy_range, seed and flexible residues if any. Ensure the whole reference ligand and plausible test ligand volume fit. Freeze a per-receptor config before native redocking; any revision changes protocol ID and triggers revalidation.

Prefer a versioned AutoDock Vina executable for the primary conventional docking path. Execute through `scripts/run_vina.py` or a documented equivalent command wrapper so the exact command, seed, config, receptor, ligand, log and return code are preserved. Do not rely on GUI state as the only record.

Run all prespecified seeds/replicates and retain modes, scores, config, receptor and ligand hashes. Do not keep only favorable runs. Compare scores only within compatible receptor, box, preparation and scoring setup; small score differences do not justify potency ranks. Secondary GNINA/DiffDock-type confidence is neither affinity nor Vina energy.
