#!/usr/bin/env bash
# Run from the WSL MD working directory.  This gate completes the restrained
# NVT/NPT pre-production equilibration and records basic QC, but never starts
# production MD.
set -euo pipefail

work_dir="/home/lg/cmpe_4kik_vitexin_equil_v2"
project_out="/mnt/c/Users/LG/.codex/.chatgpt-projects/g-p-6a855ac803f88191af36611c6ec501f3/CMPE_Docking_Revalidation/03_MD_4KIK_vitexin/pre_md_qc/structure_repair/gmx_solvated_loop_repaired/equilibration"
cd "$work_dir"

while ! grep -q "Finished mdrun" nvt.log; do
    if grep -qiE "Fatal error|LINCS WARNING|Segmentation fault" nvt.log; then
        echo "NVT gate failed: inspect nvt.log; NPT was not started." >&2
        exit 2
    fi
    sleep 120
done

if grep -qiE "Fatal error|LINCS WARNING|Segmentation fault" nvt.log; then
    echo "NVT completed with a blocking log warning; NPT was not started." >&2
    exit 2
fi

gmx grompp -f npt_restrained.mdp \
    -c nvt.gro -r em_loop_repaired_solvated.gro -t nvt.cpt \
    -p topol_equil.top -n index.ndx -o npt.tpr -maxwarn 1 \
    > npt_grompp.log 2>&1

touch NPT_STARTED
gmx mdrun -deffnm npt -ntomp 4 -pin on

if grep -qiE "Fatal error|LINCS WARNING|Segmentation fault" npt.log; then
    echo "NPT completed with a blocking log warning; pre-production QC was not marked complete." >&2
    exit 2
fi

printf "Temperature\n0\n" | gmx energy -f nvt.edr -o nvt_temperature.xvg > nvt_temperature_summary.txt 2>&1 || true
printf "Temperature\n0\n" | gmx energy -f npt.edr -o npt_temperature.xvg > npt_temperature_summary.txt 2>&1 || true
printf "Pressure\n0\n" | gmx energy -f npt.edr -o npt_pressure.xvg > npt_pressure_summary.txt 2>&1 || true
printf "Density\n0\n" | gmx energy -f npt.edr -o npt_density.xvg > npt_density_summary.txt 2>&1 || true

cp nvt.cpt nvt.edr nvt.gro nvt.log nvt.xtc npt.cpt npt.edr npt.gro npt.log npt.xtc \
   npt.tpr npt_grompp.log nvt_temperature.xvg nvt_temperature_summary.txt \
   npt_temperature.xvg npt_temperature_summary.txt npt_pressure.xvg npt_pressure_summary.txt \
   npt_density.xvg npt_density_summary.txt "$project_out"/
touch "$project_out/PRE_PRODUCTION_EQUILIBRATION_COMPLETE"
echo "NVT/NPT pre-production equilibration completed normally; production MD was not started."
