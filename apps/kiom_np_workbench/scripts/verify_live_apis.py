"""Live connectivity check for the public APIs used by KIOM NP Workbench.

This script only performs small, read-only example queries. It does not create a
project or save research data. A non-zero exit code means at least one adapter
did not return the expected response shape.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import providers


def check(name, action):
    try:
        value = action()
        if not value:
            raise RuntimeError("empty response")
        return {"status": "PASS", "records": len(value) if hasattr(value, "__len__") else None}
    except Exception as error:  # Report each provider rather than hiding later checks.
        return {"status": "FAIL", "error_type": type(error).__name__, "error": str(error)}


def main():
    results = {
        "checked_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "queries": {
            "PubChem": "naringenin",
            "EBI_OLS": "ulcerative colitis",
            "MyGene.info": ["STAT3", "JUN"],
            "STRING": ["STAT3", "JUN"],
            "g_Profiler": ["STAT3", "JUN"],
            "Open_Targets": "ulcerative colitis",
        },
    }
    results["PubChem"] = check("PubChem", lambda: providers.pubchem_compound("naringenin"))
    results["EBI_OLS"] = check("EBI OLS", lambda: providers.ols_disease("ulcerative colitis"))
    results["MyGene.info"] = check("MyGene.info", lambda: providers.mygene_map(["STAT3", "JUN"]))
    results["PubChem_active_bioassay"] = check("PubChem active bioassay", lambda: providers.pubchem_bioactivity_targets(439246))
    string_rows = []
    try:
        string_rows = providers.string_map(["STAT3", "JUN"])
        string_ids = sorted({row.get("stringId") for row in string_rows if row.get("stringId")})
        if len(string_ids) < 2:
            raise RuntimeError("fewer than two STRING IDs returned")
        edges = providers.string_network(string_ids)
        if not edges:
            raise RuntimeError("STRING network returned no edges")
        results["STRING"] = {"status": "PASS", "mapped_ids": len(string_ids), "edges": len(edges)}
    except Exception as error:
        results["STRING"] = {"status": "FAIL", "error_type": type(error).__name__, "error": str(error)}
    results["g_Profiler"] = check("g:Profiler", lambda: providers.gprofiler_enrichment(["STAT3", "JUN"]))
    results["Open_Targets"] = check("Open Targets", lambda: providers.opentargets_disease_targets("ulcerative colitis")[0])
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(row["status"] == "PASS" for name, row in results.items() if name not in {"checked_utc", "queries"}) else 1


if __name__ == "__main__":
    raise SystemExit(main())
