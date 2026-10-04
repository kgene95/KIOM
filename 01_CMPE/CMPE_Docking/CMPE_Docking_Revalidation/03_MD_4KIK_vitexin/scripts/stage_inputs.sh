#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/03_MD_4KIK_vitexin/input"
mkdir -p "$OUT"

declare -A SOURCES=(
  [20261004]="02_IKBKB_4KIK/test_ligand_docking/visualization_pdb/4KIK_vitexin_pose1_complex.pdb"
  [20261005]="02_IKBKB_4KIK/interaction_qc/plip_v301/vitexin_4_double_prime_O_glucoside_neutral_seed20261005_complex.pdb"
  [20261006]="02_IKBKB_4KIK/interaction_qc/plip_v301/vitexin_4_double_prime_O_glucoside_neutral_seed20261006_complex.pdb"
)

for seed in 20261004 20261005 20261006; do
  source_file="$ROOT/${SOURCES[$seed]}"
  target_file="$OUT/4KIK_chainB_vitexin_neutral_seed${seed}.pdb"
  test -f "$source_file"
  cp -n "$source_file" "$target_file" || true
done

(cd "$OUT" && sha256sum *.pdb > SHA256SUMS.txt)
printf 'Staged MD input coordinates in: %s\n' "$OUT"
