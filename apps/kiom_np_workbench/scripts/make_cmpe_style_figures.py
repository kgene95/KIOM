"""Create CMPE-style composite figures without changing frozen NP data.

The manuscript is used only as a visual reference. All plotted values are read
from the current project's frozen CSV outputs. The script writes a separate
reports/figures_cmpe directory and leaves the original figures untouched.
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont


def read_rows(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fnt(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\malgun.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def save_all(image: Image.Image, stem: Path) -> None:
    # PNG/TIFF are exported at 600 dpi. PDF is a rasterized publication-safe
    # companion; the source data and layout remain reproducible by this script.
    image.save(stem.with_suffix(".png"), dpi=(600, 600))
    image.save(stem.with_suffix(".tiff"), compression="tiff_lzw", dpi=(600, 600))
    image.save(stem.with_suffix(".pdf"), resolution=600.0)


def load_data(project: Path):
    hub_rows = read_rows(project / "01_np/final/hub_metrics_degree_mcc_proxy.csv")
    edge_rows = read_rows(project / "01_np/final/string_edges_score400.tsv.csv")
    enrich_rows = read_rows(project / "01_np/final/go_kegg_manuscript_filter_proxy.csv")
    hubs = [r for r in hub_rows if r.get("hub_proxy_top26") == "YES"]
    hubs.sort(key=lambda r: int(float(r.get("combined_rank", 999999))))
    hub_names = {r.get("approved_symbol", "") for r in hubs}
    edges: List[Tuple[str, str]] = []
    adjacency: Dict[str, set] = {}
    for row in edge_rows:
        a = row.get("preferredName_A", "")
        b = row.get("preferredName_B", "")
        if not a or not b:
            continue
        edges.append((a, b))
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    # Keep only non-hub connectors that touch at least two hub genes. This
    # makes a readable hub-centred subnetwork without changing the underlying
    # 95-node/639-edge PPI data.
    connector_names = {
        n for n, nbrs in adjacency.items()
        if n not in hub_names and len(nbrs & hub_names) >= 2
    }
    shown = hub_names | connector_names
    sub_edges = [(a, b) for a, b in edges if a in shown and b in shown]
    return hub_rows, hubs, enrich_rows, sub_edges, hub_names, connector_names


def draw_header(draw, title: str, subtitle: str) -> None:
    draw.text((70, 45), title, fill="#1d1d1d", font=fnt(42, True))
    draw.text((72, 100), subtitle, fill="#555555", font=fnt(22))


def make_composite(project: Path, out: Path) -> Path:
    _, hubs, enrichment, sub_edges, hub_names, connector_names = load_data(project)
    w, h = 2600, 1900
    image = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(image)
    draw_header(
        draw,
        "CMPE-style network pharmacology summary",
        "Current frozen analysis; manuscript layout used as a visual reference only",
    )

    # Panel labels and boundaries.
    draw.text((75, 160), "A", fill="#111111", font=fnt(30, True))
    draw.text((900, 160), "B", fill="#111111", font=fnt(30, True))
    draw.text((75, 1030), "C", fill="#111111", font=fnt(30, True))

    # A: hub ranking, matching the manuscript's compact hub summary.
    draw.text((125, 165), "Top hub candidates", fill="#222222", font=fnt(30, True))
    max_degree = max([int(float(r.get("degree", 0) or 0)) for r in hubs] or [1])
    # 26 rows must fit entirely above panel C; this is a layout-only setting.
    left, top, bar_w, row_h = 135, 220, 590, 27
    for i, row in enumerate(hubs):
        y = top + i * row_h
        name = row.get("approved_symbol", "")
        degree = int(float(row.get("degree", 0) or 0))
        draw.text((left, y), f"{i+1:02d} {name}", fill="#222222", font=fnt(16, i < 6))
        draw.rectangle((left + 180, y + 3, left + 180 + bar_w * degree / max_degree, y + 20), fill="#b2182b" if i < 6 else "#2166ac")
        draw.text((left + 790, y), f"DC {degree} | MCC {row.get('mcc_rank', '')}", fill="#444444", font=fnt(15))
    draw.text((135, 940), "Red: representative top hubs; blue: additional hub candidates", fill="#555555", font=fnt(17))

    # B: hub-centred PPI. The full network remains in the frozen data; this is
    # a readable manuscript panel, not a replacement for the full network.
    draw.text((950, 165), "Hub-centred STRING PPI", fill="#222222", font=fnt(30, True))
    cx, cy, radius = 1570, 570, 370
    shown = sorted(hub_names | connector_names)
    positions = {}
    hub_list = sorted(hub_names)
    for i, name in enumerate(hub_list):
        ang = 2 * math.pi * i / max(1, len(hub_list)) - math.pi / 2
        positions[name] = (cx + radius * math.cos(ang), cy + radius * math.sin(ang))
    conn_list = sorted(connector_names)
    for i, name in enumerate(conn_list):
        ang = 2 * math.pi * i / max(1, len(conn_list)) - math.pi / 2
        positions[name] = (cx + (radius - 155) * math.cos(ang), cy + (radius - 155) * math.sin(ang))
    for a, b in sub_edges:
        if a in positions and b in positions:
            draw.line([positions[a], positions[b]], fill="#cfcfcf", width=3)
    degree_by_name = {r.get("approved_symbol", ""): int(float(r.get("degree", 0) or 0)) for r in hubs}
    for name in shown:
        x, y = positions[name]
        if name in hub_names:
            rad = 14 + min(17, degree_by_name.get(name, 0) * 0.35)
            draw.ellipse((x-rad, y-rad, x+rad, y+rad), fill="#b2182b", outline="#641219", width=2)
            draw.text((x + rad + 7, y - 12), name, fill="#222222", font=fnt(18, True))
        else:
            draw.ellipse((x-8, y-8, x+8, y+8), fill="#92c5de", outline="#2166ac")
    draw.text((1000, 955), "Red: 26 hub candidates; blue: hub-connected connector nodes", fill="#555555", font=fnt(19))

    # C: compact enrichment panel from the existing filtered table.
    draw.text((125, 1035), "GO/KEGG enrichment of hub candidates", fill="#222222", font=fnt(30, True))
    parsed = []
    for row in enrichment:
        try:
            fdr = float(row.get("fdr", "inf"))
            count = int(float(row.get("hub_gene_count", 0) or 0))
        except (TypeError, ValueError):
            continue
        parsed.append((fdr, count, row.get("description", ""), row.get("category", "")))
    parsed.sort(key=lambda x: (x[0], -x[1], x[2]))
    parsed = parsed[:12]
    max_count = max([x[1] for x in parsed] or [1])
    for i, (fdr, count, desc, category) in enumerate(parsed):
        y = 1100 + i * 52
        label = desc if len(desc) <= 55 else desc[:52] + "..."
        draw.text((125, y), label, fill="#222222", font=fnt(20))
        width = 920 * count / max_count
        color = "#d6604d" if "KEGG" not in category.upper() else "#4393c3"
        draw.rectangle((780, y + 5, 780 + width, y + 29), fill=color)
        draw.text((1740, y), f"hub={count}  FDR={fdr:.2g}", fill="#444444", font=fnt(18))
    draw.text((125, 1760), "Values are read unchanged from the frozen hub/enrichment tables; no manuscript benchmark values are substituted.", fill="#555555", font=fnt(19))

    stem = out / "Fig_CMPE_style_current_analysis"
    save_all(image, stem)
    return stem


def main(project_text: str) -> None:
    project = Path(project_text)
    out = project / "reports/figures_cmpe"
    out.mkdir(parents=True, exist_ok=True)
    stem = make_composite(project, out)
    print("created", stem.with_suffix(".png"), stem.with_suffix(".tiff"), stem.with_suffix(".pdf"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/make_cmpe_style_figures.py PROJECT_DIR")
    main(sys.argv[1])
