"""Create publication-oriented NP figures from frozen current project tables.

The figures are derived from current outputs only. No canonical input is
modified. The output directory is reports/figures_cmpe_v2.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import Circle


PROJECT = Path(r"C:\Users\LG\KIOM_NP_Projects\naringenin_ulcerative_colitis_20261008_162223")
OUT = PROJECT / "reports" / "figures_cmpe_v2"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#3B76AF"
RED = "#C43C39"
PALE_BLUE = "#9EC9E3"
EDGE = "#C9C9C9"
TEXT = "#202020"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def save(fig, stem: str):
    base = OUT / stem
    fig.savefig(base.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(base.with_suffix(".tiff"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def data():
    proc = PROJECT / "01_np" / "processed"
    final = PROJECT / "01_np" / "final"
    compound_rows = read_csv(proc / "compound_target_records_qc.csv")
    disease_rows = read_csv(proc / "disease_target_records_qc.csv")
    compound = {r.get("approved_symbol", "").strip() for r in compound_rows if r.get("approved_symbol", "").strip()}
    disease = {r.get("approved_symbol", "").strip() for r in disease_rows if r.get("approved_symbol", "").strip()}
    hubs_all = read_csv(final / "hub_metrics_degree_mcc_proxy.csv")
    hubs = [r for r in hubs_all if r.get("hub_proxy_top26") == "YES"]
    hubs.sort(key=lambda r: int(float(r.get("combined_rank", 999999))))
    hub_names = {r.get("approved_symbol", "") for r in hubs}
    edges = read_csv(final / "string_edges_score400.tsv.csv")
    g = nx.Graph()
    for r in edges:
        a, b = r.get("preferredName_A", ""), r.get("preferredName_B", "")
        if a and b:
            g.add_edge(a, b)
    gp = json.loads((final / "gprofiler_enrichment.json").read_text(encoding="utf-8"))["result"]
    return compound_rows, disease_rows, compound, disease, hubs, hub_names, g, gp


def fig1_venn(compound, disease):
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    ax.set_aspect("equal")
    ax.add_patch(Circle((-0.35, 0), 1.35, facecolor="#6EA8CE", alpha=.78, edgecolor="#1F5D93", lw=2.5))
    ax.add_patch(Circle((0.35, 0), 1.35, facecolor="#EE8A67", alpha=.78, edgecolor="#A52625", lw=2.5))
    inter = len(compound & disease)
    ax.text(-0.86, 0, f"{len(compound-disease):,}", ha="center", va="center", fontsize=18, weight="bold")
    ax.text(0, 0, f"{inter:,}", ha="center", va="center", fontsize=20, weight="bold")
    ax.text(0.86, 0, f"{len(disease-compound):,}", ha="center", va="center", fontsize=18, weight="bold")
    ax.text(-.72, -1.55, f"Compound targets\n{len(compound):,}", ha="center", fontsize=12)
    ax.text(.72, -1.55, f"UC disease targets\n{len(disease):,}", ha="center", fontsize=12)
    ax.text(0, -1.95, f"Overlap genes = {inter:,}", ha="center", fontsize=13, weight="bold")
    ax.set_title("A  Compound–disease target overlap", loc="left", fontsize=16, weight="bold")
    ax.set_xlim(-1.95, 1.95); ax.set_ylim(-2.25, 1.65); ax.axis("off")
    save(fig, "Fig1_compound_disease_venn")


def fig2_compound_target(compound_rows, disease, hub_names):
    # Two compound nodes linked to the 95 overlap targets. This avoids an
    # unreadable 4,500-target hairball while preserving all source counts.
    names = {"naringenin": "Naringenin", "vitexin": "Vitexin-4\"-O-glucoside"}
    target_by_comp = {k: set() for k in names}
    for r in compound_rows:
        symbol = r.get("approved_symbol", "").strip()
        cname = (r.get("compound_name", "") or "").lower()
        key = "naringenin" if "naringenin" in cname else "vitexin" if "vitexin" in cname else None
        if key and symbol in disease:
            target_by_comp[key].add(symbol)
    targets = sorted(target_by_comp["naringenin"] | target_by_comp["vitexin"])
    g = nx.Graph()
    for key, tset in target_by_comp.items():
        g.add_node(key, bipartite=0)
        for t in tset:
            g.add_node(t, bipartite=1)
            g.add_edge(key, t)
    pos = {"naringenin": (-1.0, 0.0), "vitexin": (1.0, 0.0)}
    for i, t in enumerate(targets):
        a = 2 * math.pi * i / max(1, len(targets))
        pos[t] = (0.42 * math.cos(a), 0.95 * math.sin(a))
    fig, ax = plt.subplots(figsize=(9.0, 7.0))
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color="#BDBDBD", width=.65, alpha=.55)
    nx.draw_networkx_nodes(g, pos, nodelist=["naringenin"], node_color=RED, node_size=1300, node_shape="o", ax=ax)
    nx.draw_networkx_nodes(g, pos, nodelist=["vitexin"], node_color="#E58E2C", node_size=1300, node_shape="o", ax=ax)
    nx.draw_networkx_nodes(g, pos, nodelist=[t for t in targets if t in hub_names], node_color=RED, node_size=330, node_shape="o", ax=ax, edgecolors="#641219")
    nx.draw_networkx_nodes(g, pos, nodelist=[t for t in targets if t not in hub_names], node_color=PALE_BLUE, node_size=110, node_shape="o", ax=ax, edgecolors=BLUE, linewidths=.4)
    # Label only the most central overlap hubs here; the complete hub set is
    # shown in Fig4, avoiding an unreadable compound-target panel.
    top_hub_names = {r.get("approved_symbol", "") for r in sorted(
        [r for r in read_csv(PROJECT / "01_np/final/hub_metrics_degree_mcc_proxy.csv") if r.get("hub_proxy_top26") == "YES"],
        key=lambda r: int(float(r.get("combined_rank", 999999)))
    )[:10]}
    labels = {t: t for t in targets if t in top_hub_names}
    labels.update({"naringenin": "Naringenin", "vitexin": "Vitexin-4\"-O-glucoside"})
    nx.draw_networkx_labels(g, pos, labels=labels, font_size=8, font_weight="bold", ax=ax)
    ax.set_title("B  Compound–overlap protein network", loc="left", fontsize=16, weight="bold")
    ax.text(0, -1.18, f"Displayed targets are the {len(targets)} overlap genes; red = hub candidates", ha="center", fontsize=10)
    ax.axis("off")
    save(fig, "Fig2_compound_protein_network")


def fig3_ppi(g, hub_names):
    fig, ax = plt.subplots(figsize=(10, 8))
    pos = nx.spring_layout(g, seed=42, k=0.38, iterations=250, weight=None)
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color=EDGE, width=.45, alpha=.65)
    nonhub = [n for n in g.nodes if n not in hub_names]
    nx.draw_networkx_nodes(g, pos, nodelist=nonhub, node_color=PALE_BLUE, node_size=75, edgecolors="white", linewidths=.3, ax=ax)
    nx.draw_networkx_nodes(g, pos, nodelist=[n for n in g.nodes if n in hub_names], node_color=RED, node_size=370, edgecolors="#641219", linewidths=.6, ax=ax)
    deg = dict(g.degree())
    top_labels = {n: n for n in sorted(hub_names, key=lambda x: deg.get(x, 0), reverse=True)[:8]}
    nx.draw_networkx_labels(g, pos, labels=top_labels, font_size=8, font_weight="bold", bbox={"facecolor":"white", "edgecolor":"none", "alpha":.7, "pad":.5}, ax=ax)
    ax.set_title("C  STRING PPI network of overlap targets", loc="left", fontsize=16, weight="bold")
    isolates = 95 - g.number_of_nodes()
    ax.text(.01, -.03, f"Connected nodes = {g.number_of_nodes()}  |  Edges = {g.number_of_edges()}  |  isolates = {isolates}  |  red = 26 hub candidates", transform=ax.transAxes, fontsize=10)
    ax.axis("off")
    save(fig, "Fig3_STRING_PPI_network")


def fig4_hubs(g, hub_names, hubs):
    sub = g.subgraph(sorted(hub_names)).copy()
    fig, ax = plt.subplots(figsize=(9, 7))
    pos = nx.spring_layout(sub, seed=21, k=.65, iterations=300, weight=None)
    nx.draw_networkx_edges(sub, pos, ax=ax, edge_color="#8C8C8C", width=1.0, alpha=.8)
    sizes = {r.get("approved_symbol", ""): 350 + 15*int(float(r.get("degree", 0) or 0)) for r in hubs}
    nx.draw_networkx_nodes(sub, pos, node_color=RED, node_size=[sizes.get(n, 400) for n in sub.nodes], edgecolors="#641219", linewidths=.7, ax=ax)
    nx.draw_networkx_labels(sub, pos, font_size=9, font_weight="bold", ax=ax)
    ax.set_title("D  Hub-gene PPI subnetwork", loc="left", fontsize=16, weight="bold")
    ax.text(.01, -.03, f"Hub candidates shown = {len(sub.nodes)}  |  Edges among hubs = {sub.number_of_edges()}", transform=ax.transAxes, fontsize=10)
    ax.axis("off")
    save(fig, "Fig4_hub_gene_network")


def fig5_enrichment(gp):
    groups = [("GO:BP", "E  GO Biological Process"), ("GO:CC", "F  GO Cellular Component"), ("GO:MF", "G  GO Molecular Function"), ("KEGG", "H  KEGG pathways")]
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), constrained_layout=True)
    for ax, (source, title) in zip(axes.ravel(), groups):
        data = [r for r in gp if r.get("source") == source]
        data.sort(key=lambda r: float(r.get("p_value", 1)))
        data = data[:10][::-1]
        if not data:
            ax.text(.5, .5, "No terms in canonical output", ha="center", va="center")
            ax.set_title(title, loc="left", weight="bold")
            ax.axis("off")
            continue
        y = np.arange(len(data))
        x = np.array([int(r.get("intersection_size", 0) or 0) for r in data])
        c = -np.log10(np.array([max(float(r.get("p_value", 1)), 1e-300) for r in data]))
        sc = ax.scatter(x, y, s=45 + c*11, c=c, cmap="viridis", edgecolor="#333333", linewidth=.3)
        ax.set_yticks(y)
        ax.set_yticklabels([re.sub(r"\s+", " ", r.get("name", ""))[:43] for r in data], fontsize=8)
        ax.set_xlabel("Intersection size", fontsize=9)
        ax.set_title(title, loc="left", fontsize=13, weight="bold")
        ax.grid(axis="x", color="#E5E5E5", lw=.6)
        ax.spines[["top", "right", "left"]].set_visible(False)
        fig.colorbar(sc, ax=ax, fraction=.035, pad=.02, label="−log10(P)")
    fig.suptitle("GO/KEGG enrichment of the current STRING-mapped overlap set", fontsize=17, weight="bold", x=.05, ha="left")
    save(fig, "Fig5_GO_KEGG_dotplots")


def main():
    compound_rows, disease_rows, compound, disease, hubs, hub_names, g, gp = data()
    fig1_venn(compound, disease)
    fig2_compound_target(compound_rows, disease, hub_names)
    fig3_ppi(g, hub_names)
    fig4_hubs(g, hub_names, hubs)
    fig5_enrichment(gp)
    checks = {
        "compound_unique": len(compound),
        "disease_unique": len(disease),
        "overlap": len(compound & disease),
        "string_nodes": g.number_of_nodes(),
        "string_edges": g.number_of_edges(),
        "hub_candidates": len(hub_names),
        "figures": sorted(p.name for p in OUT.glob("Fig*")),
    }
    (OUT / "figure_qc.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
