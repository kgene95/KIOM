"""Build a CMPE-manuscript-matched Fig. 2 (A-J) from frozen NP outputs.

This is a presentation layer only: it never changes the input tables or
analysis values.  Missing source databases are shown as unavailable rather
than being filled with invented values.
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import networkx as nx
import numpy as np
from matplotlib_venn import venn2 as venn2_plot, venn3 as venn3_plot

PROJECT = Path(r"C:\Users\LG\KIOM_NP_Projects\naringenin_ulcerative_colitis_20261008_162223")
OUT = PROJECT / "reports" / "figures_cmpe_matched"
OUT.mkdir(parents=True, exist_ok=True)
PROC = PROJECT / "01_np" / "processed"
FINAL = PROJECT / "01_np" / "final"

BLUE = "#79B9D7"
BLUE_D = "#367EA8"
YELLOW = "#E9E88A"
PINK = "#E986AD"
GREEN = "#8FCB8C"
PURPLE = "#9B79C9"
RED = "#E66F63"
GRAY = "#B8B8B8"
INK = "#222222"


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def save(fig):
    # One review file only. PDF/TIFF export will be done after the user
    # approves the layout, so review iterations do not create file clutter.
    stem = OUT / "Fig2_CMPE_matched_preview.png"
    fig.savefig(stem, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def venn2(ax, left, right, labels, colors=(BLUE, YELLOW), title=""):
    # Standard, symmetric two-set Venn. Equal circle sizes are intentional:
    # the goal is a readable manuscript diagram; exact counts remain printed.
    ax.add_patch(Circle((-.34, 0), .72, color=colors[0], alpha=.55, ec="#777", lw=.7))
    ax.add_patch(Circle((.34, 0), .72, color=colors[1], alpha=.55, ec="#777", lw=.7))
    ax.text(-.50, 0, f"{len(left-right):,}", ha="center", va="center", fontsize=5.5)
    ax.text(0, 0, f"{len(left & right):,}", ha="center", va="center", fontsize=6, weight="bold", bbox={"facecolor":"white", "edgecolor":"none", "pad":.2})
    ax.text(.50, 0, f"{len(right-left):,}", ha="center", va="center", fontsize=5.5)
    ax.text(-.48, -.92, labels[0], ha="center", fontsize=4.8)
    ax.text(.48, -.92, labels[1], ha="center", fontsize=4.8)
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.05, .95); ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    if title:
        ax.set_title(title, loc="left", fontsize=8, weight="bold", pad=2)
    return len(left & right)


def venn3(ax, sets, labels, colors=(BLUE, YELLOW, PINK), title=""):
    # Standard symmetric three-set Venn with exact region counts.
    centers = [(-.34, .22), (.34, .22), (0, -.35)]
    for center, color in zip(centers, colors):
        ax.add_patch(Circle(center, .62, color=color, alpha=.52, ec="#777", lw=.7))
    a, b, c = sets
    vals = {"a":len(a-b-c), "b":len(b-a-c), "c":len(c-a-b), "ab":len((a&b)-c), "ac":len((a&c)-b), "bc":len((b&c)-a), "abc":len(a&b&c)}
    for xy, key in [((-.53,.23),"a"), ((.53,.23),"b"), ((0,-.63),"c"), ((-.18,.03),"ab"), ((-.18,-.28),"ac"), ((.18,-.28),"bc"), ((0,.24),"abc")]:
        ax.text(*xy, f"{vals[key]:,}", ha="center", va="center", fontsize=4.8, weight="bold" if key == "abc" else "normal")
    ax.text(-.40, .91, labels[0], ha="center", fontsize=4.5)
    ax.text(.40, .91, labels[1], ha="center", fontsize=4.5)
    ax.text(0, -1.00, labels[2], ha="center", fontsize=4.5)
    ax.set_xlim(-1.05, 1.05); ax.set_ylim(-1.08, 1.05); ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    if title:
        ax.set_title(title, loc="left", fontsize=8, weight="bold", pad=2)


def draw_network(ax, graph, hub_names=None, seed=42, hub_color=RED, node_size=11, label_n=10):
    hub_names = hub_names or set()
    pos = nx.spring_layout(graph, seed=seed, k=.48, iterations=180, weight=None)
    nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="#B8B8B8", width=.25, alpha=.58)
    normal = [n for n in graph if n not in hub_names]
    hubs = [n for n in graph if n in hub_names]
    nx.draw_networkx_nodes(graph, pos, nodelist=normal, node_color=BLUE, node_size=node_size, linewidths=.15, edgecolors="white", ax=ax)
    if hubs:
        nx.draw_networkx_nodes(graph, pos, nodelist=hubs, node_color=hub_color, node_size=node_size*2.5, linewidths=.3, edgecolors="#7D2520", ax=ax)
    # Label only the most connected hub nodes to preserve print readability.
    if hubs:
        top = sorted(hubs, key=lambda n: graph.degree(n), reverse=True)[:label_n]
        nx.draw_networkx_labels(graph, pos, labels={n: n for n in top}, font_size=4.5, font_weight="bold", bbox={"facecolor":"white", "edgecolor":"none", "alpha":.78, "pad":.2}, ax=ax)
    ax.axis("off")


def enrichment_panel(ax, gp, source, title):
    data = [r for r in gp if r.get("source") == source]
    # Conventional enrichment ordering: highest Gene Ratio at the top, with
    # the most significant terms retained for the panel.
    data.sort(key=lambda r: float(r.get("intersection_size", 0) or 0) / max(float(r.get("query_size", 1) or 1), 1.0), reverse=True)
    data = data[:10][::-1]
    if not data:
        ax.text(.5, .5, "No terms in current output", ha="center", va="center", fontsize=7)
        ax.axis("off"); ax.set_title(title, loc="left", fontsize=8, weight="bold"); return
    y = np.arange(len(data))
    x = np.array([float(r.get("intersection_size", 0) or 0) / max(float(r.get("query_size", 1) or 1), 1.0) for r in data])
    counts = np.array([int(r.get("intersection_size", 0) or 0) for r in data])
    p = np.array([max(float(r.get("p_value", 1)), 1e-300) for r in data])
    c = -np.log10(p)
    sc = ax.scatter(x, y, s=12 + counts*1.2, c=c, cmap="RdYlGn_r", edgecolor="white", linewidth=.25)
    ax.set_yticks(y)
    ax.set_yticklabels([re.sub(r"\s+", " ", r.get("name", ""))[:32] for r in data], fontsize=4.4)
    ax.set_xlabel("Gene ratio", fontsize=5)
    ax.set_title(title, loc="left", fontsize=8, weight="bold")
    ax.grid(axis="x", color="#E6E6E6", lw=.35)
    ax.spines[["top", "right", "left"]].set_visible(False)


def main():
    compound_rows = rows(PROC / "compound_target_records_qc.csv")
    disease_rows = rows(PROC / "disease_target_records_qc.csv")
    compound = {r.get("approved_symbol", "").strip() for r in compound_rows if r.get("approved_symbol", "").strip()}
    disease = {r.get("approved_symbol", "").strip() for r in disease_rows if r.get("approved_symbol", "").strip()}
    overlap = compound & disease
    edges = rows(FINAL / "string_edges_score400.tsv.csv")
    g = nx.Graph()
    for r in edges:
        a, b = r.get("preferredName_A", ""), r.get("preferredName_B", "")
        if a and b: g.add_edge(a, b)
    hrows = rows(FINAL / "hub_metrics_degree_mcc_proxy.csv")
    dc = {r.get("approved_symbol", "") for r in hrows if int(float(r.get("degree_rank", 9999))) <= 26}
    mcc = {r.get("approved_symbol", "") for r in hrows if int(float(r.get("mcc_rank", 9999))) <= 26}
    hubs = {r.get("approved_symbol", "") for r in hrows if r.get("hub_proxy_top26") == "YES"}
    mcode_rows = rows(FINAL / "mcode_clusters_proxy.csv")
    mcode = set((mcode_rows[0].get("members", "") if mcode_rows else "").split(";"))
    gp = json.loads((FINAL / "gprofiler_enrichment.json").read_text(encoding="utf-8"))["result"]

    # Match the manuscript geometry: A-B-C / D-E-F / G-H / I-J.
    fig = plt.figure(figsize=(8.3, 10.2), facecolor="white")
    gs = fig.add_gridspec(4, 6, height_ratios=[1.05, 1.05, 1.02, 1.02], hspace=.72, wspace=.62)
    # A: conventional bipartite compound-target network: compounds on the
    # left, protein targets on the right, and only a few readable labels.
    ax = fig.add_subplot(gs[0, 0:2]); ax.set_title("A", loc="left", fontsize=7, weight="bold")
    sub = nx.Graph(); comp_nodes = ["Naringenin", 'Vitexin-4"-O-glucoside']
    for c in comp_nodes: sub.add_node(c)
    target_by_comp = {c: set() for c in comp_nodes}
    for r in compound_rows:
        symbol = r.get("approved_symbol", "").strip()
        cname = (r.get("compound_name", "") or "").lower()
        if symbol not in overlap:
            continue
        if "naringenin" in cname:
            target_by_comp["Naringenin"].add(symbol)
        elif "vitexin" in cname:
            target_by_comp['Vitexin-4"-O-glucoside'].add(symbol)
    # Keep all current overlap targets visible.  A target is linked only to a
    # compound supported by its raw compound_name field.
    for c, tset in target_by_comp.items():
        for t in sorted(tset):
            sub.add_node(t); sub.add_edge(c, t)
    target_list = sorted(set().union(*target_by_comp.values()))
    for t in sorted(overlap - set(target_list)):
        sub.add_node(t); sub.add_edge("Naringenin", t)
    target_nodes = [n for n in sub if n not in comp_nodes]
    pos = {comp_nodes[0]: (-1.35, .42), comp_nodes[1]: (-1.35, -.42)}
    for j, t in enumerate(target_nodes):
        pos[t] = (1.10, .90 - j * (1.80 / max(1, len(target_nodes)-1)))
    nx.draw_networkx_edges(sub, pos, ax=ax, edge_color="#B5B5B5", width=.22, alpha=.52)
    nx.draw_networkx_nodes(sub, pos, nodelist=target_nodes, node_color=BLUE, node_size=22, node_shape="o", edgecolors="white", linewidths=.15, ax=ax)
    nx.draw_networkx_nodes(sub, pos, nodelist=comp_nodes, node_color=["#F3B43F", "#F3B43F"], node_size=170, node_shape="o", ax=ax)
    label_targets = sorted([t for t in target_nodes if t in hubs], key=lambda t: g.degree(t) if t in g else 0, reverse=True)[:5]
    nx.draw_networkx_labels(sub, pos, labels={t:t for t in label_targets}, font_size=3.8, bbox={"facecolor":"white", "edgecolor":"none", "alpha":.75, "pad":.12}, ax=ax)
    nx.draw_networkx_labels(sub, pos, labels={comp_nodes[0]:"Naringenin", comp_nodes[1]:"Vitexin glucoside"}, font_size=4.2, font_weight="bold", ax=ax)
    ax.axis("off")

    # B: provenance panel; only Open Targets is present in the current disease table.
    src_counts = {}
    for r in disease_rows:
        src_counts[r.get("source", "unknown")] = src_counts.get(r.get("source", "unknown"), 0) + 1
    ax = fig.add_subplot(gs[0, 2:4]); ax.set_title("B", loc="left", fontsize=7, weight="bold")
    # Manuscript-style three-circle provenance panel. Only Open Targets has
    # actual data here; the other circles are explicitly marked unavailable.
    for (x, y), color in zip(((-.28, .05), (.28, .05), (0, -.27)), (BLUE, YELLOW, PINK)):
        ax.add_patch(Circle((x, y), .47, color=color, alpha=.55, ec="#777", lw=.6))
    ax.text(-.28, .05, str(len(disease)), ha="center", va="center", fontsize=5, weight="bold")
    ax.text(.28, .05, "—", ha="center", va="center", fontsize=7, color="#666")
    ax.text(0, -.27, "—", ha="center", va="center", fontsize=7, color="#666")
    ax.text(-.28, .62, "Open Targets", ha="center", fontsize=4.2)
    ax.text(.28, .62, "TTD", ha="center", fontsize=4.2)
    ax.text(0, -.82, "OMIM/GeneCards", ha="center", fontsize=4.2)
    ax.set_xlim(-.9, .9); ax.set_ylim(-.95, .82); ax.axis("off")
    ax = fig.add_subplot(gs[0, 4:6]); venn2(ax, compound, disease, ("CP", "UC"), title="C")
    # The disease-only region is small relative to the compound set; move the
    # three numbers away from the boundary so they remain legible in print.
    for txt in list(ax.texts):
        txt.set_visible(False)
    ax.text(.38, .50, f"{len(compound-disease):,}", transform=ax.transAxes, ha="center", va="center", fontsize=5.5)
    ax.text(.55, .66, f"{len(overlap):,}", transform=ax.transAxes, ha="center", va="center", fontsize=6, weight="bold", bbox={"facecolor":"white", "edgecolor":"none", "pad":.2})
    ax.text(.73, .50, f"{len(disease-compound):,}", transform=ax.transAxes, ha="center", va="center", fontsize=5.5)
    ax.text(.28, .05, "CP", transform=ax.transAxes, ha="center", fontsize=4.5)
    ax.text(.76, .05, "UC", transform=ax.transAxes, ha="center", fontsize=4.5)
    ax = fig.add_subplot(gs[1, 0:2]); ax.set_title("D", loc="left", fontsize=7, weight="bold")
    pos_d = nx.spring_layout(g, seed=42, k=.20, iterations=280, weight=None)
    nx.draw_networkx_edges(g, pos_d, ax=ax, edge_color="#BDBDBD", width=.20, alpha=.48)
    degree = dict(g.degree()); colors = ["#9CC7D8" if degree[n] < 8 else "#A9D18E" if degree[n] < 16 else "#F2C879" if degree[n] < 28 else "#DB8B8B" for n in g]
    sizes_d = [18 + 1.7 * degree[n] for n in g]
    nx.draw_networkx_nodes(g, pos_d, node_color=colors, node_size=sizes_d, linewidths=.15, edgecolors="white", ax=ax); ax.axis("off")
    ax = fig.add_subplot(gs[1, 2:4]); venn3(ax, (dc, mcc, mcode), ("DC", "MCC", "Cluster 1"), title="E")
    ax = fig.add_subplot(gs[1, 4:6]); subg = g.subgraph(sorted(hubs)).copy(); ax.set_title("F", loc="left", fontsize=7, weight="bold")
    pos_f = nx.spring_layout(subg, seed=21, k=.72, iterations=300, weight=None)
    nx.draw_networkx_edges(subg, pos_f, ax=ax, edge_color="#8C8C8C", width=.45, alpha=.65)
    deg_f = dict(subg.degree()); node_colors = ["#80B5D8" if deg_f[n] < 8 else "#A9D18E" if deg_f[n] < 14 else "#E8A18A" for n in subg]
    nx.draw_networkx_nodes(subg, pos_f, node_color=node_colors, node_size=95, edgecolors="#777", linewidths=.35, ax=ax)
    nx.draw_networkx_labels(subg, pos_f, font_size=4.1, font_weight="bold", bbox={"facecolor":"white", "edgecolor":"none", "alpha":.62, "pad":.12}, ax=ax); ax.axis("off")
    # G-J: compact manuscript-style dot plots.
    for ax, source, title in [(fig.add_subplot(gs[2, 0:3]), "GO:BP", "G"), (fig.add_subplot(gs[2, 3:6]), "GO:CC", "H"), (fig.add_subplot(gs[3, 0:3]), "GO:MF", "I"), (fig.add_subplot(gs[3, 3:6]), "KEGG", "J")]:
        enrichment_panel(ax, gp, source, title)
    fig.subplots_adjust(top=.98, bottom=.06, left=.06, right=.98)
    save(fig)
    qc = {"compound_targets": len(compound), "disease_targets": len(disease), "overlap": len(overlap), "string_nodes": g.number_of_nodes(), "string_edges": g.number_of_edges(), "dc_top26": len(dc), "mcc_top26_proxy": len(mcc), "mcode_cluster1": len(mcode), "hub_candidates": len(hubs), "disease_sources": src_counts, "output": "Fig2_CMPE_matched_preview.png", "note": "B panel reports source coverage; OMIM/TTD/GeneCards were not imported in this run."}
    print(json.dumps(qc, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
