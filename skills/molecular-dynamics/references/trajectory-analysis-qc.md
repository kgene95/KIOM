# Trajectory analysis and convergence QC

Use this reference after a production trajectory exists and basic run-integrity checks pass.

## Pre-analysis integrity

Use the topology that exactly matches trajectory atom order. Confirm time units, frame spacing, box vectors, periodic-boundary handling, and whether the trajectory has been made whole/centered consistently. Preserve an untouched raw trajectory and perform analysis on derived copies.

Do not combine alignment and periodic-contact calculations carelessly: a trajectory rotated for RMSD/RMSF analysis may no longer be appropriate for minimum-image distance analysis unless the box treatment is also valid.

## Core observables

Select observables before interpreting stability:

- protein backbone or C-alpha RMSD after justified alignment;
- ligand heavy-atom RMSD using a clearly defined protein-aligned or ligand-internal reference;
- per-residue RMSF after alignment;
- protein-ligand contact occupancy by residue with an explicit atom selection and distance cutoff;
- hydrogen-bond occupancy/time series with donor/acceptor and geometry definitions;
- selected mechanistically justified distances or angles;
- radius of gyration, secondary structure, PCA, clustering, or population-derived free-energy surfaces only when they answer a stated question.

Do not treat a flat RMSD trace by itself as proof of binding stability.

## Equilibration and convergence

Identify and justify any discarded equilibration/burn-in window. Inspect observables in time blocks rather than only whole-trajectory means. Where feasible, estimate autocorrelation/effective sample size or compare block means/uncertainty. For replicate simulations, report between-replicate consistency and disagreement rather than pooling traces blindly.

A trajectory is not "converged" merely because temperature/density stabilized or because one RMSD trace plateaued. Use multiple observables and adequate sampling for the scientific question.

## Contact and interaction claims

Report occupancy denominators, analyzed frames, cutoff/geometry, atom selections, and whether periodic boundaries were used. Distinguish persistent, intermittent, and replicate-specific contacts. A contact/hydrogen bond in MD supports a modeled interaction pattern, not experimental target engagement or affinity.

## Free-energy surface and advanced analysis

A free-energy surface derived from trajectory populations is a descriptive projection of sampled states. State collective variables, binning/kernel method, temperature, and sampling limitations. Do not call it a binding free energy calculation.

MM/PBSA, MM/GBSA, alchemical FEP/TI, metadynamics, umbrella sampling, or residence-time analyses require separate prespecified methods and validation; do not infer them from ordinary production MD.

## Reproducible outputs

Preserve analysis selections, commands/scripts, software versions, frame range, stride, raw numeric tables, and figure source. Report units explicitly. Use the same frozen analysis definition across compared systems unless a justified exception is documented.
