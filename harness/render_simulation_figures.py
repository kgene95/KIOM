from pathlib import Path
import json, math, html
import pandas as pd

ROOT = Path(r"D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\simulations\CMPE_UC_real_data_acceptance")
OUT = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)

def esc(x): return html.escape(str(x))
def write_svg(name, body, width, height):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><style>text{{font-family:Arial,sans-serif;fill:#222}} .grid{{stroke:#e5e5e5;stroke-width:1}} .title{{font-size:18px;font-weight:bold}} .label{{font-size:12px}} .small{{font-size:10px}}</style>{body}</svg>'
    (OUT / name).write_text(svg, encoding="utf-8")

mcc = pd.read_csv(ROOT / "cytoscape" / "primary" / "mcc_rank.csv")
enrich = pd.read_csv(ROOT / "analysis" / "cmpe_union_string_enrichment.tsv", sep="\t")
enrich["fdr"] = pd.to_numeric(enrich["fdr"], errors="coerce").clip(lower=1e-300)
enrich["neglog10_fdr"] = -enrich["fdr"].map(math.log10)
enrich["gene_ratio"] = enrich["number_of_genes"] / enrich["number_of_genes_in_background"]

# A: MCC horizontal bars
top = mcc.sort_values(["mcc_score","maximal_clique_count"], ascending=False).head(20).sort_values("mcc_score")
W,H=900,720; left, right, topm, bottom = 190, 35, 55, 45
plotw=W-left-right; ploth=H-topm-bottom; row=ploth/20
mx=float(top.mcc_score.max())
parts=[f'<text x="{W/2}" y="28" text-anchor="middle" class="title">CMPE–UC integrated PPI: top 20 MCC-ranked targets</text>']
for i in range(6):
    x=left+plotw*i/5
    parts.append(f'<line x1="{x:.1f}" y1="{topm}" x2="{x:.1f}" y2="{H-bottom}" class="grid"/>')
for i, r in enumerate(top.itertuples()):
    y=topm+(i+.5)*row
    bw=plotw*float(r.mcc_score)/mx
    parts.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" class="label">{esc(r.gene)}</text>')
    parts.append(f'<rect x="{left}" y="{y-row*.32:.1f}" width="{bw:.1f}" height="{row*.64:.1f}" fill="#c75b63"/>')
parts.append(f'<text x="{W/2}" y="{H-10}" text-anchor="middle" class="label">MCC score (independent maximal-clique calculation)</text>')
write_svg("Figure_A_MCC_top20.svg","".join(parts),W,H)

# B: four enrichment panels, 7 terms each
W,H=1200,900; pw,ph=560,390
parts=[f'<text x="{W/2}" y="25" text-anchor="middle" class="title">CMPE–UC enrichment preview: top 7 terms per category</text>']
panels=[("Process","GO Biological Process"),("Component","GO Cellular Component"),("Function","GO Molecular Function"),("KEGG","KEGG pathway")]
for pi,(cat,title) in enumerate(panels):
    ox=(pi%2)*pw; oy=45+(pi//2)*ph
    d=enrich[enrich.category==cat].sort_values(["fdr","number_of_genes"]).head(7).copy()
    parts.append(f'<text x="{ox+pw/2}" y="{oy+20}" text-anchor="middle" class="title">{title}</text>')
    if d.empty:
        parts.append(f'<text x="{ox+pw/2}" y="{oy+ph/2}" text-anchor="middle">No source rows</text>'); continue
    d["label"]=d["description"].fillna(d["term"]).astype(str).str.slice(0,48)
    d=d.sort_values("gene_ratio"); maxr=max(float(d.gene_ratio.max()),1e-9)
    for j,r in enumerate(d.itertuples()):
        y=oy+55+j*38; x=ox+180+(pw-230)*float(r.gene_ratio)/maxr
        radius=5+12*float(r.number_of_genes)/max(float(d.number_of_genes.max()),1)
        color="#cf6357" if float(r.neglog10_fdr)>10 else "#e79a68"
        parts.append(f'<line x1="{ox+180}" y1="{y}" x2="{ox+pw-30}" y2="{y}" class="grid"/>')
        parts.append(f'<text x="{ox+172}" y="{y+4}" text-anchor="end" class="small">{esc(r.label)}</text>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y}" r="{radius:.1f}" fill="{color}" stroke="#555" stroke-width=".6"><title>FDR={r.fdr}; genes={r.number_of_genes}; gene ratio={r.gene_ratio:.4f}</title></circle>')
    parts.append(f'<text x="{ox+pw/2}" y="{oy+ph-14}" text-anchor="middle" class="label">Gene ratio; circle size = gene count; color = −log10(FDR)</text>')
write_svg("Figure_B_GO_KEGG_top7.svg","".join(parts),W,H)

summary=json.loads((ROOT/"simulation_summary.json").read_text(encoding="utf-8"))
W,H=900,420; labels=["STRING nodes","STRING edges","Enrichment rows","MCC rows"]; vals=[summary["string_nodes"],summary["string_edges"],len(enrich),summary["mcc_rows"]]; mx=max(vals)
parts=[f'<text x="{W/2}" y="28" text-anchor="middle" class="title">Simulation acceptance: generated analysis artifacts</text>']
for i,(lab,val) in enumerate(zip(labels,vals)):
    x=80+i*205; h=280*val/mx; y=345-h; color=["#5b8db8","#5b8db8","#77a974","#c75b63"][i]
    parts += [f'<rect x="{x}" y="{y:.1f}" width="120" height="{h:.1f}" fill="{color}"/>',f'<text x="{x+60}" y="{y-8:.1f}" text-anchor="middle" class="label">{val:,}</text>',f'<text x="{x+60}" y="370" text-anchor="middle" class="label">{esc(lab)}</text>']
write_svg("Figure_C_artifact_counts.svg","".join(parts),W,H)

manifest={"source":"simulation_summary.json, mcc_rank.csv, cmpe_union_string_enrichment.tsv","figures":["Figure_A_MCC_top20.svg","Figure_B_GO_KEGG_top7.svg","Figure_C_artifact_counts.svg"],"note":"SVG figures are generated from simulation artifacts; they do not alter source calculations. GUI visual review remains pending."}
(OUT/"figure_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False))

