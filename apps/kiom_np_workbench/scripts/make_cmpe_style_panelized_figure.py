"""Create a panelized CMPE-style figure from frozen current NP outputs.

Panel order: A Venn, B hub-centred PPI, C GO-BP, D GO-CC, E GO-MF, F KEGG.
This is a visualization-only derivative; source CSV/TSV/GraphML files are not
modified and manuscript benchmark counts are never substituted.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont


def rows(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def font(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\malgun.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def save_formats(image: Image.Image, stem: Path) -> None:
    image.save(stem.with_suffix(".png"), dpi=(600, 600))
    image.save(stem.with_suffix(".tiff"), compression="tiff_lzw", dpi=(600, 600))
    image.save(stem.with_suffix(".pdf"), resolution=600.0)


def load(project: Path):
    proc = project / "01_np/processed"
    final = project / "01_np/final"
    compound = {r.get("approved_symbol", "").strip() for r in rows(proc / "compound_target_records_qc.csv") if r.get("approved_symbol", "").strip()}
    disease = {r.get("approved_symbol", "").strip() for r in rows(proc / "disease_target_records_qc.csv") if r.get("approved_symbol", "").strip()}
    hubs_all = rows(final / "hub_metrics_degree_mcc_proxy.csv")
    hubs = [r for r in hubs_all if r.get("hub_proxy_top26") == "YES"]
    hubs.sort(key=lambda r: int(float(r.get("combined_rank", 999999))))
    hub_names = {r.get("approved_symbol", "") for r in hubs}
    edges = []
    adj: Dict[str, set] = {}
    for r in rows(final / "string_edges_score400.tsv.csv"):
        a, b = r.get("preferredName_A", ""), r.get("preferredName_B", "")
        if not a or not b:
            continue
        edges.append((a, b))
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    connectors = {n for n, ns in adj.items() if n not in hub_names and len(ns & hub_names) >= 2}
    shown = hub_names | connectors
    sub_edges = [(a, b) for a, b in edges if a in shown and b in shown]
    # The filtered manuscript proxy contains only COMPARTMENTS and KEGG rows.
    # Use the canonical g:Profiler result for the requested GO BP/CC/MF panels.
    gprofiler = json.loads((final / "gprofiler_enrichment.json").read_text(encoding="utf-8"))["result"]
    return compound, disease, hubs, hub_names, connectors, sub_edges, gprofiler


def panel_title(draw, x, y, letter, title):
    draw.text((x, y), letter, fill="#111111", font=font(30, True))
    draw.text((x + 48, y + 2), title, fill="#222222", font=font(27, True))


def draw_venn(draw, box, compound, disease):
    x0, y0, x1, y1 = box
    panel_title(draw, x0, y0, "A", "Compound–disease overlap")
    cx1, cx2, cy = x0 + 185, x0 + 330, y0 + 260
    r = 170
    draw.ellipse((cx1-r, cy-r, cx1+r, cy+r), fill="#7fb3d5", outline="#2166ac", width=4)
    draw.ellipse((cx2-r, cy-r, cx2+r, cy+r), fill="#ef8a62", outline="#b2182b", width=4)
    inter = len(compound & disease)
    left = len(compound - disease)
    right = len(disease - compound)
    draw.text((cx1-120, cy-30), str(left), fill="#111111", font=font(30, True))
    draw.text((cx2-22, cy-30), str(right), fill="#111111", font=font(30, True))
    draw.text((cx1+72, cy-30), str(inter), fill="#111111", font=font(30, True))
    draw.text((x0+55, y0+465), f"Compound targets  {len(compound):,}", fill="#333333", font=font(19))
    draw.text((x0+55, y0+495), f"Disease targets  {len(disease):,}", fill="#333333", font=font(19))
    draw.text((x0+55, y0+525), f"Overlap  {inter:,}", fill="#333333", font=font(19, True))


def draw_ppi(draw, box, hubs, hub_names, connectors, sub_edges):
    x0, y0, x1, y1 = box
    panel_title(draw, x0, y0, "B", "Hub-centred STRING PPI")
    cx, cy = (x0+x1)//2, y0+285
    radius = 225
    positions = {}
    hlist = sorted(hub_names)
    for i, name in enumerate(hlist):
        a = 2 * math.pi * i / max(1, len(hlist)) - math.pi / 2
        positions[name] = (cx + radius*math.cos(a), cy + radius*math.sin(a))
    clist = sorted(connectors)
    for i, name in enumerate(clist):
        a = 2 * math.pi * i / max(1, len(clist)) - math.pi / 2
        positions[name] = (cx + (radius-95)*math.cos(a), cy + (radius-95)*math.sin(a))
    for a, b in sub_edges:
        if a in positions and b in positions:
            draw.line((positions[a], positions[b]), fill="#d0d0d0", width=2)
    deg = {r.get("approved_symbol", ""): int(float(r.get("degree", 0) or 0)) for r in hubs}
    for name, (x, y) in positions.items():
        if name in hub_names:
            rad = 11 + min(16, deg.get(name, 0)*0.3)
            draw.ellipse((x-rad, y-rad, x+rad, y+rad), fill="#b2182b", outline="#641219", width=2)
            draw.text((x+rad+4, y-9), name, fill="#222222", font=font(15, True))
        else:
            draw.ellipse((x-6, y-6, x+6, y+6), fill="#92c5de", outline="#2166ac")
    draw.text((x0+50, y1-38), "Red: 26 hub candidates; blue: hub-connected nodes", fill="#555555", font=font(17))


def draw_enrich(draw, box, letter, title, data):
    x0, y0, x1, y1 = box
    panel_title(draw, x0, y0, letter, title)
    data = sorted(data, key=lambda r: (float(r[0]), -int(r[1]), r[2]))[:6]
    max_count = max([int(r[1]) for r in data] or [1])
    top = y0 + 70
    for i, (fdr, count, desc) in enumerate(data):
        y = top + i*52
        label = desc if len(desc) <= 37 else desc[:34] + "..."
        draw.text((x0+35, y), label, fill="#222222", font=font(17))
        width = 270 * int(count) / max_count
        draw.rectangle((x0+300, y+4, x0+300+width, y+27), fill="#d6604d")
        draw.text((x0+590, y), f"n={count}; P={float(fdr):.2g}", fill="#444444", font=font(15))


def main(project_text: str):
    project = Path(project_text)
    out = project / "reports/figures_cmpe"
    out.mkdir(parents=True, exist_ok=True)
    compound, disease, hubs, hub_names, connectors, sub_edges, enrich = load(project)
    w, h = 2600, 2450
    image = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 38), "CMPE-style network pharmacology analysis", fill="#111111", font=font(42, True))
    draw.text((72, 92), "Current frozen analysis; values are not replaced by manuscript benchmark values", fill="#555555", font=font(21))
    # 2 x 3 panel order: Venn, PPI, GO-BP, GO-CC, GO-MF, KEGG.
    boxes = [(70, 155, 820, 910), (870, 155, 2530, 910), (70, 1010, 870, 2240), (920, 1010, 1720, 2240), (1770, 1010, 2530, 2240)]
    draw_venn(draw, boxes[0], compound, disease)
    draw_ppi(draw, boxes[1], hubs, hub_names, connectors, sub_edges)
    groups = {"BP": [], "CC": [], "MF": [], "KEGG": []}
    for r in enrich:
        cat = (r.get("source", "") or "").upper()
        key = "BP" if cat == "GO:BP" else "CC" if cat == "GO:CC" else "MF" if cat == "GO:MF" else "KEGG" if cat == "KEGG" else None
        if key:
            try:
                groups[key].append((float(r.get("p_value", "inf")), int(r.get("intersection_size", 0) or 0), r.get("name", "")))
            except (TypeError, ValueError):
                pass
    # The lower row has three GO panels plus KEGG in a compact right-side strip.
    draw_enrich(draw, (70, 1010, 870, 2240), "C", "GO Biological Process", groups["BP"])
    draw_enrich(draw, (920, 1010, 1720, 2240), "D", "GO Cellular Component", groups["CC"])
    draw_enrich(draw, (1770, 1010, 2530, 1580), "E", "GO Molecular Function", groups["MF"])
    draw_enrich(draw, (1770, 1640, 2530, 2240), "F", "KEGG pathways", groups["KEGG"])
    draw.text((70, 2365), "Source: current project canonical CSV outputs. Figure layout is a CMPE-style reconstruction; original manuscript benchmark counts are not used.", fill="#555555", font=font(18))
    stem = out / "Fig_CMPE_style_panelized_current_analysis"
    save_formats(image, stem)
    print("created", *(str(stem.with_suffix(ext)) for ext in (".png", ".tiff", ".pdf")))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/make_cmpe_style_panelized_figure.py PROJECT_DIR")
    main(sys.argv[1])
