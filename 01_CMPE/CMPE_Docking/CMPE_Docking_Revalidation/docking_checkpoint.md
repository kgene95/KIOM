# Docking checkpoint index

Read `00_PROJECT/CURRENT_STATUS.md` first.  This root-level file is an index for cross-agent handoff; receptor-level checkpoints and manifests remain the authoritative calculation records.

- **4KIK / IKKβ:** native KSA redocking PASS (0.3808 Å); neutral vitexin and naringenin top poses have PASS seed consistency, PLIP interaction XML, and clash/pocket QC; interpretation remains conditional on neutral protonation and is not evidence of binding.
- **5IKR / COX-2:** BLOCKED before native ID8 redocking because COH handling has not been parameterized or justified.
- **Figure:** review composition only; final export and manuscript prose are pending QC completion and user approval.
- **Pre-MD strain screen:** isolated-ligand MMFF94 relaxation completed for all neutral seeds; screening-only, not a final force-field strain result.
- **Vitexin atom mapping:** PASS for docking pose 1 against the clean PubChem graph: 42/42 heavy-atom `SMILES IDX`/element checks, 72-atom explicit-H rebuild, AM1-BCC charge transfer, GAFF2 typing, and `parmchk2` completed.
- **4KIK–vitexin MD entry:** PASS for the neutral-vitexin modeled-loop branch.  PDBFixer rebuilt only internal chain-B residues 174–176, 373–375, and 551–557 while preserving 5,270 deposited atoms exactly; Amber14SB/phosaa14SB/GAFF2 topology and a neutral, 366,069-atom TIP3P system passed unrestrained PME minimization at `emtol = 1000` (Fmax 969.362 after 2,114 steps).  Restrained NVT and NPT each completed for 100 ps without fatal/LINCS errors; production MD and trajectory stability analysis have not started.
