# Pose QC and interpretation

Inspect pocket occupancy, clashes, pose outside the validated pocket, ligand strain and implausible geometry, pose clustering/top-mode consistency, key residues, cofactor/metal geometry and known catalytic site. Record H-bonds, hydrophobic contacts, pi interactions, salt bridges, metal/cofactor contacts and pocket location with a versioned deterministic tool or documented GUI/version and explicit criteria. Inspect suspicious hydrogens, charge, covalent artifacts and tautomer assumptions. Interaction diagrams are descriptive, not proof.

Across multiple seeds, report pose/interaction consistency rather than a single favorable run. If top-ranked modes disagree strongly across seeds, flag instability rather than selecting the most visually attractive pose.

Separate computed prediction from mechanism. Use `predicted binding`, `favorable docking pose`, `plausible interaction`, or `testable interaction hypothesis requiring biochemical/functional validation`. Never state inhibition, direct binding, target engagement, pathway regulation or stronger biological activity was demonstrated by a docking score. Prior scores are historical; compare only with method/protocol differences stated, without pooling as replicates.
