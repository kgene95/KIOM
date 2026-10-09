"""Recompute hub metrics and manuscript-style GO/KEGG filtering.

This is a terminal-reproducible proxy for the CytoHubba MCC score.  The
installed Cytoscape MCODE app is run separately through cyREST and its exact
output is stored as ``mcode_clusters_cytoscape_2.0.3.csv``.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def maximal_cliques(graph):
    """Bron-Kerbosch maximal cliques for this 95-node STRING graph."""
    result = []

    def visit(current, candidates, excluded):
        if not candidates and not excluded:
            result.append(frozenset(current))
            return
        pivot_pool = candidates | excluded
        pivot = max(pivot_pool, key=lambda node: len(graph[node])) if pivot_pool else None
        choices = candidates - (graph[pivot] if pivot else set())
        for node in list(choices):
            visit(current | {node}, candidates & graph[node], excluded & graph[node])
            candidates.remove(node)
            excluded.add(node)

    visit(set(), set(graph), set())
    return result


def mcode_proxy_clusters(graph, minimum_size=3):
    """Deterministic MCODE-like seed-and-grow clusters, explicitly a proxy."""
    weights = {}
    for node, neighbors in graph.items():
        degree = len(neighbors)
        possible = degree * (degree - 1) / 2
        internal = sum(1 for a in neighbors for b in graph[a] if b in neighbors and a < b)
        density = internal / possible if possible else 0.0
        weights[node] = degree * density
    clusters = []
    assigned = set()
    for seed in sorted(graph, key=lambda n: (-weights[n], n)):
        if weights[seed] <= 0:
            continue
        cutoff = weights[seed] * 0.2
        members = {seed} | {n for n in graph[seed] if weights.get(n, 0) >= cutoff}
        if len(members) < minimum_size:
            continue
        density_edges = sum(1 for a in members for b in graph[a] if b in members and a < b)
        density = density_edges / (len(members) * (len(members) - 1) / 2)
        if density < 0.2 or members <= assigned:
            continue
        cluster_id = len(clusters) + 1
        clusters.append({"cluster_id": cluster_id, "seed": seed, "size": len(members), "density": round(density, 6), "members": sorted(members)})
        assigned |= members
    return clusters


def main(project_text: str):
    project = Path(project_text)
    edge_path = project / "01_np/final/string_edges_score400.tsv.csv"
    enrichment_path = project / "01_np/final/string_enrichment.tsv.csv"
    if not edge_path.exists() or not enrichment_path.exists():
        raise FileNotFoundError("STRING edge/enrichment output is missing")

    graph = defaultdict(set)
    for row in read_rows(edge_path):
        a = (row.get("preferredName_A") or "").strip()
        b = (row.get("preferredName_B") or "").strip()
        if a and b and a != b:
            graph[a].add(b)
            graph[b].add(a)
    graph = {node: set(neighbors) for node, neighbors in graph.items()}
    cliques = maximal_cliques(graph)
    mcc = defaultdict(float)
    for clique in cliques:
        contribution = math.factorial(max(0, len(clique) - 1))
        for node in clique:
            mcc[node] += contribution
    degree = {node: len(neighbors) for node, neighbors in graph.items()}
    degree_order = sorted(graph, key=lambda node: (-degree[node], node))
    mcc_order = sorted(graph, key=lambda node: (-mcc[node], node))
    degree_rank = {node: index + 1 for index, node in enumerate(degree_order)}
    mcc_rank = {node: index + 1 for index, node in enumerate(mcc_order)}
    combined_order = sorted(graph, key=lambda node: (degree_rank[node] + mcc_rank[node], node))
    hub_proxy = set(combined_order[:26])
    clusters = mcode_proxy_clusters(graph)
    cluster_by_node = {}
    for cluster in clusters:
        for node in cluster["members"]:
            cluster_by_node.setdefault(node, []).append(cluster["cluster_id"])
    hub_rows = []
    for node in sorted(graph, key=lambda n: (not (n in hub_proxy), degree_rank[n], n)):
        hub_rows.append({
            "approved_symbol": node,
            "degree": degree[node],
            "degree_rank": degree_rank[node],
            "mcc": int(mcc[node]),
            "mcc_rank": mcc_rank[node],
            "combined_rank": degree_rank[node] + mcc_rank[node],
            "hub_proxy_top26": "YES" if node in hub_proxy else "NO",
            "mcode_proxy_clusters": ";".join(map(str, cluster_by_node.get(node, []))),
            "method": "terminal MCC proxy; CytoHubba GUI MCC was not exposed by cyREST",
        })
    final = project / "01_np/final"
    write_rows(final / "hub_metrics_degree_mcc_proxy.csv", hub_rows, list(hub_rows[0]))
    write_rows(
        final / "cytohubba_mcc_terminal_reproduction.csv",
        [{
            "name": row["approved_symbol"],
            "mcc": row["mcc"],
            "mcc_rank": row["mcc_rank"],
            "method": "Independent reproduction of the CytoHubba MCC formula from the frozen STRING graph; terminal execution",
        } for row in hub_rows],
        ["name", "mcc", "mcc_rank", "method"],
    )
    cluster_rows = []
    for cluster in clusters:
        cluster_rows.append({"cluster_id": cluster["cluster_id"], "seed": cluster["seed"], "size": cluster["size"], "density": cluster["density"], "members": ";".join(cluster["members"]), "method": "MCODE-like terminal proxy; not Cytoscape MCODE"})
    write_rows(final / "mcode_clusters_proxy.csv", cluster_rows, ["cluster_id", "seed", "size", "density", "members", "method"])

    excluded_words = ("cancer", "infection", "infectious", "disease-specific")
    filtered = []
    for row in read_rows(enrichment_path):
        category = (row.get("category") or "").upper()
        description = (row.get("description") or "").strip()
        if not (category.startswith("BIOLOGICAL_PROCESS") or category.startswith("MOLECULAR_FUNCTION") or category.startswith("COMPARTMENTS") or category.startswith("KEGG")):
            continue
        try:
            fdr = float(row.get("fdr") or "inf")
        except ValueError:
            continue
        if fdr >= 0.01 or any(word in description.lower() for word in excluded_words):
            continue
        genes = {gene.strip().upper() for gene in (row.get("preferredNames") or "").split(",") if gene.strip()}
        hub_genes = sorted(genes & {node.upper() for node in hub_proxy})
        if len(hub_genes) < 3:
            continue
        filtered.append({**row, "hub_gene_count": len(hub_genes), "hub_genes": ";".join(hub_genes), "filter_rule": "FDR < 0.01; >=3 proxy hub genes; cancer/infection/disease-specific terms excluded"})
    if filtered:
        write_rows(final / "go_kegg_manuscript_filter_proxy.csv", filtered, list(filtered[0]))
    else:
        write_rows(final / "go_kegg_manuscript_filter_proxy.csv", [], list(read_rows(enrichment_path)[0]) + ["hub_gene_count", "hub_genes", "filter_rule"])
    summary = {"method": "independent reproduction of CytoHubba MCC formula", "nodes": len(graph), "edges": sum(len(v) for v in graph.values()) // 2, "proxy_hub_count": len(hub_proxy), "mcode_proxy_clusters": len(clusters), "filtered_go_kegg_terms": len(filtered), "manuscript_parameters": {"fdr_lt": 0.01, "minimum_hub_genes": 3, "excluded_term_keywords": list(excluded_words)}, "limitations": ["The CytoHubba GUI plugin was not executed because its v0.1 release targets Cytoscape 3.0; this table is an independent reproduction of the published MCC formula on the frozen STRING graph.", "Exact Cytoscape MCODE 2.0.3 output is stored separately and should be used for MCODE claims."]}
    (final / "hub_enrichment_proxy_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/run_hub_and_manuscript_enrichment.py PROJECT_DIR")
    main(sys.argv[1])
