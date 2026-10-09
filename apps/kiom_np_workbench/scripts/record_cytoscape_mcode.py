"""Record a verified Cytoscape MCODE cyREST run in the NP manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import analysis_review_findings, file_sha, load_json, now, save_json


def main(project_text: str) -> None:
    project = Path(project_text)
    manifest_path = project / "00_project" / "NP_manifest.json"
    manifest = load_json(manifest_path, {})
    raw_path = project / "01_np/final/mcode_cytoscape_2.0.3_raw.json"
    csv_path = project / "01_np/final/mcode_clusters_cytoscape_2.0.3.csv"
    mcc_path = project / "01_np/final/cytohubba_mcc_terminal_reproduction.csv"
    if not raw_path.exists() or not csv_path.exists() or not mcc_path.exists():
        raise FileNotFoundError("MCODE output files are missing")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    clusters = raw.get("response", {}).get("data", {}).get("clusters", [])
    run = {
        "provider": "Cytoscape MCODE",
        "status": "COMPLETED",
        "version": "2.0.3",
        "network_id": raw.get("network_id"),
        "clusters": len(clusters),
        "parameters": raw.get("parameters", {}),
        "execution": "local cyREST",
        "updated_utc": now(),
    }
    runs = [item for item in manifest.get("provider_runs", []) if item.get("provider") != "Cytoscape MCODE"]
    runs.append(run)
    manifest["provider_runs"] = runs
    manifest["hub_analysis"] = {
        "cytoscape_mcode": "COMPLETED",
        "cytoscape_mcode_version": "2.0.3",
        "cytoscape_mcode_csv": "01_np/final/mcode_clusters_cytoscape_2.0.3.csv",
        "cytoscape_mcode_raw_json": "01_np/final/mcode_cytoscape_2.0.3_raw.json",
        "cytohubba_mcc": "NOT_EXECUTED_GUI_ONLY",
        "cytohubba_mcc_proxy": "01_np/final/hub_metrics_degree_mcc_proxy.csv",
        "cytohubba_mcc_terminal_reproduction": "01_np/final/cytohubba_mcc_terminal_reproduction.csv",
    }
    entries = {str(item.get("path", "")).replace("\\", "/"): item for item in manifest.get("files", [])}
    for path in (csv_path, raw_path, mcc_path):
        rel = str(path.relative_to(project)).replace("\\", "/")
        entries[rel] = {"path": rel, "sha256": file_sha(path)}
    manifest["files"] = list(entries.values())
    manifest["analysis_updated_utc"] = now()
    manifest["review_findings"] = analysis_review_findings(manifest)
    save_json(manifest_path, manifest)
    print(json.dumps({"provider": run["provider"], "status": run["status"], "clusters": run["clusters"], "network_id": run["network_id"]}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/record_cytoscape_mcode.py PROJECT_DIR")
    main(sys.argv[1])
