# Fig. 3(B) docking result summary

## Scope

This summary replaces the historical IKKβ `3RZF` docking interpretation with the validated human IKKβ `4KIK` chain-B protocol. It is a computational revalidation of the docking result and does not establish binding, inhibition, or target engagement.

## Locked calculation

- Receptor: human IKKβ `4KIK`, chain B
- Native control: KSA native-ligand redocking; symmetry-aware heavy-atom RMSD `0.3808 Å` (PASS; prespecified gate ≤2.0 Å)
- Engine: AutoDock Vina `1.2.7`
- Grid: `30 × 30 × 30 Å`, protocol `4KIK_B_VINA_30A_EX32`
- Exhaustiveness: `32`; modes: `20`
- Independent seeds: `20261004`, `20261005`, `20261006`
- Primary ligand state: neutral vitexin-4″-O-glucoside; PubChem CID `56776173`
- Comparator: neutral naringenin; PubChem CID `439246`

## Primary pose and score summary

| Ligand | Seed scores (kcal/mol) | Mean ± SD (kcal/mol) | Range | Pose consistency | Pose QC |
|---|---:|---:|---:|---|---|
| Vitexin-4″-O-glucoside | −10.452, −10.442, −10.458 | −10.451 ± 0.008 | −10.458 to −10.442 | direct heavy-atom RMSD 0.0485–0.1088 Å | PASS |
| Naringenin | −9.329, −9.322, −9.289 | −9.313 ± 0.021 | −9.329 to −9.289 | direct heavy-atom RMSD 0.0201–0.0461 Å | PASS |

The neutral vitexin primary poses were approximately `1.14 kcal/mol` more favorable than the neutral naringenin comparator under this fixed protocol. This score difference is protocol- and protonation-state-specific and should not be presented as an experimental affinity or proof of stronger biological activity.

## Interaction and geometry QC

- Vitexin top poses: 12–13 hydrogen bonds, 6 hydrophobic interactions, minimum protein distance 2.471–2.493 Å, zero heavy-atom contacts below 1.5 Å, and 41/42 ligand heavy atoms within 5 Å of protein atoms.
- Naringenin top poses: 6–8 hydrogen bonds, 9 hydrophobic interactions, minimum protein distance 2.707–2.726 Å, zero heavy-atom contacts below 1.5 Å, and 20/20 ligand heavy atoms within 5 Å.
- PLIP `3.0.1` XML interaction records and seedwise pose QC passed for all six neutral top poses.
- Independent ligand-strain minimization and charged-state sensitivity are not complete; the interpretation remains conditional on the neutral state.

## Manuscript-safe conclusion

The reanalysis supports replacing the historical 3RZF receptor with human 4KIK chain B for the Fig. 3(B) computational panel. KSA redocking reproduced the native pose, and the three-seed neutral vitexin poses were highly reproducible and geometrically compatible with the IKKβ pocket. The result supports a reproducible docking hypothesis for follow-up work; it does not demonstrate physical binding or inhibition.

## Source records

- `02_IKBKB_4KIK/docking_results.csv`
- `02_IKBKB_4KIK/test_ligand_docking/neutral_primary_results.csv`
- `02_IKBKB_4KIK/redocking/KSA_redocking_30A_symmetry_rmsd.csv`
- `02_IKBKB_4KIK/interaction_qc/plip_v301/interaction_summary_seedwise.csv`
- `02_IKBKB_4KIK/interaction_qc/plip_v301/pose_qc_seedwise.csv`
- `02_IKBKB_4KIK/figure_drafts/Fig3B_4KIK_vitexin_COMPOSITION_DRAFT_v2.png`
