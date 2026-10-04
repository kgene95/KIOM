# Docking revalidation checkpoint — current endpoint

## Completed

- Human IKKβ 4KIK chain B receptor preparation and KSA native-ligand redocking.
- Final 30 Å grid validation: top KSA pose symmetry-aware heavy-atom RMSD 0.3808 Å; PASS at the ≤2.0 Å gate.
- Neutral state-8 vitexin-4″-O-glucoside and naringenin docking with three independent seeds each.
- Separate monoanionic vitexin sensitivity runs for states 4, 6, and 7.
- Deterministic clash and 5 Å pocket-occupancy QC for all six neutral top poses; minimum protein distance 2.471–2.726 Å and zero heavy-atom contacts below 1.5 Å.
- Top-pose replicate consistency for all neutral seeds: naringenin direct-coordinate heavy-atom RMSD `0.0201–0.0461 Å`; vitexin `0.0485–0.1088 Å` in the shared receptor/grid frame.
- PLIP 3.0.1 XML interaction fingerprints for all six neutral top poses; seedwise summaries are in `02_IKBKB_4KIK/interaction_qc/plip_v301/`.
- Manifest SHA256 validation.

## Current interpretation boundary

Vitexin is the primary CMPE ligand for interpretation; naringenin is a comparator. The neutral results are conditional computational results under the locked 4KIK protocol. Scores must not be described as experimental binding affinities or proof of target engagement.

## Closed 4KIK job, with retained limitations

- Ligand strain has not been independently minimized or quantified; the current PASS is limited to pose consistency, PLIP interaction parsing, clash screen, and pocket occupancy.
- 5IKR COX-2 native-ID8 redocking remains BLOCKED until the deposited COH metalloporphyrin receives a reviewed local template and defensible Vina atom/scoring treatment.
- Historical manuscript IKKβ docking scores have been transcribed into `integration/previous_vs_current.csv`. They remain methodologically non-comparable with the 4KIK/Vina values; COX-2 and BCL-2 remain historical-only until a separate validated reanalysis is completed.
- Publication figure export and manuscript wording remain pending review of the original figure and explicit composition approval.
