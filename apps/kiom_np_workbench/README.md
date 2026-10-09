# KIOM NP Workbench — Full workflow build

Windows local Streamlit application. Copy the folder to a durable drive (for example `D:\KIOM_NP_Workbench`), run `setup_windows.bat` once, then `run_windows.bat`. The server window must remain open while the app is used.

## Included
- PubChem chemical identity lookup and EBI OLS disease concept lookup
- Draft autosave, project creation/opening, manifests, checkpoints, logs, raw-export preservation
- One-click automatic starting evidence: active PubChem bioassay targets and Open Targets disease-target associations; optional source CSV intake for supplementary evidence
- MyGene.info symbol/Entrez mapping, species and ambiguity QC, broad exploratory overlap
- STRING ID mapping, PPI and STRING enrichment adapters; g:Profiler GO/KEGG/Reactome adapter
- Cytoscape GraphML and node/edge CSV exports
- Project-local NP skill addendum: `docs/NP_SKILL_ADDENDUM.md` (source provenance, ZIP/TSV intake, QC gate, hub and enrichment reporting contract)
- Optional human transcriptomics branch: deferred/skipped/reviewed DEG import, or local R/limma on a normalized log-scale expression matrix with two groups
- PowerShell live-log command and CLI execution logs for limma

## Scientific and technical limits
- API adapters are implemented but **must be live-tested on the target PC and their returned versions/ID mapping checked** before publication use.
- The automatic compound branch retrieves **observed active PubChem bioassay targets**, not in-silico target predictions. A PubChem target enters the human overlap only after single human MyGene mapping. It is evidence discovery, not proof of direct binding or a complete target panel.
- The automatic disease branch uses Open Targets Platform GraphQL association scores. It is a starting evidence source, not a replacement for disease-specific curation. SwissTargetPrediction, PharmMapper, SEA, OMIM, TTD, GeneCards and other sources remain optional user-export imports; no unapproved web-form scraping is performed.
- In **Upload source files** mode, the app provides an in-page guide for SwissTargetPrediction, SEA, and PharmMapper. Download each original result yourself and upload one file per compound/source; preserve native target IDs, scores/ranks, species, job URL, and source columns. Do not enter a personal email address in the app or a source CSV. If PharmMapper asks for email, provide it only on PharmMapper's own form.
- Overlap is labeled broad exploratory pending full source-panel and mapping review; it is never auto-promoted to primary.
- Transcriptomics is optional and separately branched. Local limma accepts normalized log-scale expression values only. Raw-count DESeq2 and automatic GEO study selection/QC are not implemented. Rscript and Bioconductor limma must be installed locally.
- No docking or MD is executed. GraphML is a Cytoscape input network, not a Cytoscape-generated analysis or final figure.
- Existing v1 project folders are not migrated automatically. Choose the old project folder in the sidebar to continue browsing it only if its manifest schema is compatible; otherwise retain it separately and migrate source files deliberately.

## Local installation and verification

1. Double-click `setup_windows.bat` once. It creates `.venv` and installs the pinned dependency ranges. If the folder was copied from another location, do not copy its old `.venv`: rename that disposable folder and run setup again.
2. In the project folder, open PowerShell (click the folder address bar, type `powershell`, press Enter) and run the following commands one at a time. Each command should finish without `FAIL` or `ERROR`.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\verify_live_apis.py
```

The live check makes small read-only example queries to PubChem, EBI OLS, MyGene.info, STRING, g:Profiler, and Open Targets. Record its JSON output with the project records before using those API results in a publication.

3. Start the web app by double-clicking `run_windows.bat`. The launcher first checks Python, dependencies, write access, and whether port 8501 is already occupied. Only after `PREFLIGHT OK` will Streamlit start. The terminal should then display a local URL such as `http://localhost:8501`; keep that window open and open the URL in a browser. If the preflight reports that port 8501 is already in use, do not start a second copy; close the existing Streamlit terminal or use its already-open browser tab.

Human transcriptomics remains optional: it is not run by either verification command and stays in the separate `02_transcriptomics` branch.
