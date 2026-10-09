"""Run the installed Cytoscape MCODE app through its local cyREST API."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


BASE = "http://localhost:1234"


def api(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(BASE + path, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(project_text):
    project = Path(project_text)
    graphml = project / "03_cytoscape/network.graphml"
    final = project / "01_np/final"
    if not graphml.exists():
        raise FileNotFoundError(graphml)
    loaded = api("/v1/commands/network/load%20file", {"file": str(graphml)})
    network_id = loaded["data"]["networks"][0]
    # Supplying only the network lets the installed MCODE app apply its own
    # GUI defaults and returns those effective parameters in the response.
    # cyREST's MCODE command expects the network selector as a string.  A
    # numeric JSON value is parsed as a floating-point setting by Cytoscape
    # and causes HTTP 500 ("Couldn't parse value ... for setting: Network").
    result = api("/v1/commands/mcode/cluster", {"network": str(network_id)})
    params = result["data"].get("parameters", {"network": network_id})
    table = api(f"/v1/networks/{network_id}/tables/defaultnode")["rows"]
    suid_to_name = {str(row["SUID"]): row.get("name", "") for row in table}
    edge_rows = read_csv(project / "01_np/final/string_edges_score400.tsv.csv")
    ens_to_symbol = {}
    for row in edge_rows:
        for ens, symbol in ((row.get("stringId_A", ""), row.get("preferredName_A", "")), (row.get("stringId_B", ""), row.get("preferredName_B", ""))):
            if ens and symbol:
                ens_to_symbol[ens] = symbol
    cluster_rows = []
    for cluster in result["data"].get("clusters", []):
        symbols = [ens_to_symbol.get(suid_to_name.get(str(node), ""), suid_to_name.get(str(node), "")) for node in cluster.get("nodes", [])]
        cluster_rows.append({"rank": cluster.get("rank"), "name": cluster.get("name"), "score": cluster.get("score"), "seed_node_suid": cluster.get("seedNode"), "seed_symbol": ens_to_symbol.get(suid_to_name.get(str(cluster.get("seedNode")), ""), suid_to_name.get(str(cluster.get("seedNode")), "")), "size": len(symbols), "members": ";".join(sorted(filter(None, symbols))), "cytoscape_network_id": network_id, "mcode_version": "2.0.3", "parameters": json.dumps(params, ensure_ascii=False)} )
    write_csv(final / "mcode_clusters_cytoscape_2.0.3.csv", cluster_rows, list(cluster_rows[0]) if cluster_rows else ["rank", "name", "score", "seed_node_suid", "seed_symbol", "size", "members", "cytoscape_network_id", "mcode_version", "parameters"])
    (final / "mcode_cytoscape_2.0.3_raw.json").write_text(json.dumps({"network_id": network_id, "parameters": params, "response": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"network_id": network_id, "mcode_version": "2.0.3", "clusters": len(cluster_rows), "cluster_sizes": [row["size"] for row in cluster_rows]}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/run_cytoscape_mcode.py PROJECT_DIR")
    main(sys.argv[1])
