"""Create dependency-light manuscript figures from frozen NP outputs."""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\malgun.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def save_network(project: Path, out: Path):
    hub = rows(project / "01_np/final/hub_metrics_degree_mcc_proxy.csv")
    edges = rows(project / "01_np/final/string_edges_score400.tsv.csv")
    nodes = sorted({r.get("preferredName_A", "") for r in edges} | {r.get("preferredName_B", "") for r in edges})
    nodes = [n for n in nodes if n]
    hubs = {r["approved_symbol"] for r in hub if r.get("hub_proxy_top26") == "YES"}
    w, h = 2200, 1700
    image = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 45), "STRING PPI network with independent MCC hub candidates", fill="#111111", font=font(42, True))
    cx, cy = w // 2, h // 2 + 60
    radius = min(w, h) * 0.36
    pos = {node: (cx + radius * math.cos(2 * math.pi * i / max(1, len(nodes))), cy + radius * math.sin(2 * math.pi * i / max(1, len(nodes)))) for i, node in enumerate(nodes)}
    for edge in edges:
        a, b = edge.get("preferredName_A", ""), edge.get("preferredName_B", "")
        if a in pos and b in pos:
            draw.line([pos[a], pos[b]], fill="#d9d9d9", width=2)
    degree = {r["approved_symbol"]: int(float(r.get("degree", 0) or 0)) for r in hub}
    for node, (x, y) in pos.items():
        is_hub = node in hubs
        r = 9 + min(20, degree.get(node, 0) * 0.35) if is_hub else 6
        fill = "#d73027" if is_hub else "#74add1"
        draw.ellipse((x-r, y-r, x+r, y+r), fill=fill, outline="#333333")
        if is_hub:
            draw.text((x + 12, y - 12), node, fill="#111111", font=font(20, True))
    draw.rectangle((80, h-115, 112, h-83), fill="#d73027", outline="#333333")
    draw.text((125, h-115), "Top 26 hub candidates (independent MCC + degree ranking)", fill="#111111", font=font(24))
    draw.rectangle((80, h-70, 112, h-38), fill="#74add1", outline="#333333")
    draw.text((125, h-70), "Other STRING-mapped nodes", fill="#111111", font=font(24))
    image.save(out)


def save_hubs(project: Path, out: Path):
    data = [r for r in rows(project / "01_np/final/hub_metrics_degree_mcc_proxy.csv") if r.get("hub_proxy_top26") == "YES"]
    data.sort(key=lambda r: int(r.get("combined_rank", 999999)))
    w, h = 1900, 1400
    image = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 40), "Top 26 hub candidates", fill="#111111", font=font(44, True))
    max_degree = max(int(float(r.get("degree", 0) or 0)) for r in data) if data else 1
    left, top, bar_w, row_h = 400, 125, 1150, 42
    for i, row in enumerate(data):
        y = top + i * row_h
        name = row["approved_symbol"]
        degree = int(float(row.get("degree", 0) or 0))
        draw.text((70, y+4), f"{i+1:02d}  {name}", fill="#111111", font=font(23, True if i < 10 else False))
        draw.rectangle((left, y+4, left + bar_w * degree / max_degree, y+30), fill="#d73027" if i < 10 else "#74add1")
        draw.text((left + bar_w + 18, y+3), f"degree {degree} | MCC rank {row.get('mcc_rank')}", fill="#333333", font=font(20))
    draw.text((70, h-55), "Ranking: combined degree rank + independent MCC rank; plugin GUI not executed", fill="#555555", font=font(22))
    image.save(out)


def save_enrichment(project: Path, out: Path):
    data = []
    for row in rows(project / "01_np/final/go_kegg_manuscript_filter_proxy.csv"):
        try:
            fdr = float(row.get("fdr", "inf"))
        except ValueError:
            continue
        data.append((fdr, row.get("description", ""), row.get("category", ""), int(float(row.get("hub_gene_count", 0) or 0))))
    data.sort(key=lambda x: (x[0], -x[3], x[1]))
    data = data[:20]
    w, h = 2200, 1400
    image = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 40), "Manuscript-style GO/KEGG enrichment", fill="#111111", font=font(42, True))
    left, top, plot_w, row_h = 700, 125, 1100, 52
    max_count = max([x[3] for x in data] or [1])
    for i, (fdr, desc, category, count) in enumerate(data):
        y = top + i * row_h
        label = desc if len(desc) <= 58 else desc[:55] + "..."
        draw.text((65, y+4), label, fill="#111111", font=font(21))
        width = plot_w * count / max_count
        color = "#4575b4" if "KEGG" in category.upper() else "#f46d43"
        draw.rectangle((left, y+8, left + width, y+33), fill=color)
        draw.text((left + plot_w + 18, y+3), f"hub={count}; FDR={fdr:.2g}", fill="#333333", font=font(19))
    draw.text((70, h-55), "Filter: FDR < 0.01; >=3 hub genes; cancer/infection/disease-specific terms excluded", fill="#555555", font=font(20))
    image.save(out)


def main(project_text: str):
    project = Path(project_text)
    out = project / "reports/figures"
    out.mkdir(parents=True, exist_ok=True)
    save_network(project, out / "Fig1_STRING_PPI_hub_candidates.png")
    save_hubs(project, out / "Fig2_top26_hub_candidates.png")
    save_enrichment(project, out / "Fig3_GO_KEGG_enrichment_hub_filtered.png")
    print("created", *(str(p) for p in sorted(out.glob("Fig*.png"))))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/make_np_figures.py PROJECT_DIR")
    main(sys.argv[1])
