# Molecular docking audit

## Receptor identity and structure selection

Check target identity, PDB ID, experimental method, resolution when applicable, chain, biological relevance, bound ligand/cofactor, missing residues, mutations, and selection rationale. Distinguish experimentally known binding sites from predicted/blind pockets.

## Ligand identity and preparation

Check exact ligand identity, stereochemistry, protonation/tautomer assumptions, charge, source identifier, and preparation tool/version when reported. Flag silent isomer or protonation substitutions.

## Protocol and search space

Check engine/version, receptor/ligand preparation, grid center/dimensions or pocket definition, exhaustiveness/search parameters, random seed, number of poses, energy range, and output selection rule. Missing details reduce reproducibility even when a score is reported.

## Validation gate

When a suitable co-crystallized ligand exists, look for redocking before interpreting test-ligand docking. Check the RMSD definition and value; <=2 A is a common practical criterion but must not be treated as a universal law. If redocking failed, test docking from that protocol is not validated. If no native ligand exists, require an explicit alternate validation rationale and limitation.

## Test docking and pose QC

Check that the reported score belongs to the displayed/selected pose. Examine pose consistency, severe clashes, implausible torsions/strain when data permit, and whether repeated seeds/runs support a stable pose. Do not treat a more negative Vina score as experimental affinity.

## Interaction analysis

Check residue identity, chain, interaction type, distance/geometry when available, and consistency between pose files, interaction tables, figures, and Results text. Flag decorative interaction diagrams that cannot be traced to a pose.

## Interpretation

Allowed: docking supports a structurally plausible binding hypothesis or relative pose/score within the stated protocol.

Not allowed without independent evidence: docking proves binding, inhibition, target engagement, mechanism, or in vivo efficacy.
