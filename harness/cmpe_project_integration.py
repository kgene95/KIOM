"""Project-level integration for an extract paper with multiple constituents.

Child NP runs remain independently traceable.  This worker creates the paper
level CMPE view only after every child run has a verified Cytoscape degree
artifact and completion gate.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def integrate(project_dir: Path) -> dict:
    project_path = project_dir / "project.json"
    project = read_json(project_path)
    if not project:
        raise FileNotFoundError(project_path)
    run_root = project_dir.parent.parent / "runs"
    run_ids = list(project.get("run_ids", []))
    if len(run_ids) < 2:
        raise ValueError("CMPE project requires at least two constituent runs")

    compound_rows: dict[str, list[dict]] = {}
    child_meta = []
    blockers = []
    for run_id in run_ids:
        run = run_root / run_id
        request = read_json(run / "request.json")
        state = read_json(run / "harness_state.json")
        degree_path = run / "cytoscape" / "primary" / "degree_rank.csv"
        if state.get("status") != "COMPLETE":
            blockers.append(f"{run_id}: harness_state={state.get('status', 'missing')}")
        if not degree_path.is_file():
            blockers.append(f"{run_id}: degree_rank.csv missing")
            continue
        rows = []
        with degree_path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                gene = (row.get("gene") or "").strip()
                if not gene:
                    continue
                rows.append({"gene": gene, "degree": float(row.get("degree") or 0), "rank": len(rows) + 1})
        label = request.get("compound_title") or request.get("compound_input") or run_id
        cid = str(request.get("compound_cid") or "")
        compound_key = f"{label} (CID {cid})" if cid else str(label)
        compound_rows[compound_key] = rows
        child_meta.append({"run_id": run_id, "compound": compound_key, "cid": cid,
                           "degree_rank": str(degree_path), "hub_count": len(rows),
                           "figure_draft": (run / "figure_draft.md").is_file(),
                           "completion_manifest": (run / "completion_manifest.json").is_file()})
    if blockers:
        raise RuntimeError("; ".join(blockers))

    by_gene: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for compound, rows in compound_rows.items():
        for row in rows:
            by_gene[row["gene"]].append((compound, row))
    integrated = []
    top10_sets = {compound: {r["gene"] for r in rows[:10]} for compound, rows in compound_rows.items()}
    shared_top10 = set.intersection(*top10_sets.values()) if top10_sets else set()
    for gene, members in by_gene.items():
        ranks = {compound: row["rank"] for compound, row in members}
        degrees = {compound: row["degree"] for compound, row in members}
        integrated.append({"gene": gene, "compounds": "; ".join(sorted(ranks)),
                           "compound_count": len(ranks), "mean_degree": round(sum(degrees.values()) / len(degrees), 3),
                           "min_rank": min(ranks.values()), "rank_by_compound": json.dumps(ranks, ensure_ascii=False),
                           "hub_class": "shared_top10" if gene in shared_top10 else ("shared" if len(ranks) > 1 else "compound_specific")})
    integrated.sort(key=lambda r: (-r["compound_count"], r["min_rank"], -r["mean_degree"], r["gene"]))

    csv_path = project_dir / "cmpe_hub_genes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["gene", "compounds", "compound_count", "mean_degree", "min_rank", "rank_by_compound", "hub_class"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(integrated)
    shared = [row for row in integrated if row["hub_class"] == "shared_top10"]
    report = project_dir / "cmpe_hub_summary.md"
    lines = ["# CMPE 통합 허브 유전자 요약", "", "CMPE는 두 성분을 하나의 추출물 연구 단위로 통합한다. 성분별 run은 독립적으로 보존하고, 이 문서는 두 run의 Cytoscape primary degree 결과를 논문 수준에서 연결한 통합 요약이다.", "", f"- 질환: {project.get('disease', 'Ulcerative colitis')}", f"- 성분 run 수: {len(compound_rows)}", f"- 공통 Top-10 허브: {len(shared)}개", "", "## 공통 Top-10 허브", "", "| 유전자 | 포함 성분 | 평균 degree | 성분별 rank |", "|---|---|---:|---|"]
    for row in shared:
        lines.append(f"| {row['gene']} | {row['compounds']} | {row['mean_degree']} | {row['rank_by_compound']} |")
    lines += ["", "## 성분별 Top-10", ""]
    for compound, rows in compound_rows.items():
        lines += [f"### {compound}", "", "| 순위 | 유전자 | degree |", "|---:|---|---:|"]
        lines += [f"| {r['rank']} | {r['gene']} | {r['degree']:g} |" for r in rows[:10]]
        lines.append("")
    lines += ["## 해석 경계", "", "공통 허브는 현재 frozen STRING/Cytoscape 네트워크의 topology 요약이다. 질환 특이성, 직접 결합, 활성화·억제를 단독으로 증명하지 않으며, 도킹 후보 선정과 실제 도킹은 별도 검증 단계다."]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    figure = project_dir / "cmpe_figure_draft.md"
    figure_lines = ["# CMPE 논문용 Figure 통합 초안", "", "두 성분을 별도 논문으로 나누지 않고 하나의 CMPE 추출물 연구로 제시하는 Figure 구성이다.", "", "| 패널 | 내용 | 근거 |", "|---|---|---|", "| A | CMPE 추출물 → 두 성분 → 질환 표적 → 통합 PPI workflow | 두 child run과 project manifest |", "| B | 두 성분별 PPI 네트워크 | 각 child Cytoscape primary manifest |", "| C | 공통 허브와 성분별 허브 비교 | `cmpe_hub_genes.csv` |", "| D | 공통/성분별 enrichment 비교 | 각 child enrichment artifact |", "| E | CMPE 통합 후보·후속 도킹 handoff | 성분별 예비 후보와 공통 허브 |", "", "각 child Figure 초안은 child run에 보존하고, 이 문서는 논문용 통합 배치만 정의한다. 실제 도킹 계산은 별도 workflow다."]
    figure.write_text("\n".join(figure_lines) + "\n", encoding="utf-8")

    manifest = {"status": "PROJECT_INTEGRATED", "project_id": project.get("project_id"), "extract": "CMPE", "disease": project.get("disease", "Ulcerative colitis"), "run_ids": run_ids, "constituents": child_meta, "shared_top10_hub_genes": [r["gene"] for r in shared], "artifacts": ["cmpe_hub_genes.csv", "cmpe_hub_summary.md", "cmpe_figure_draft.md"], "updated_utc": now_utc()}
    write_json(project_dir / "cmpe_project_manifest.json", manifest)
    project.update({"name": "CMPE · Ulcerative colitis · 2 constituents", "status": "PROJECT_INTEGRATED", "disease": "Ulcerative colitis", "extract": "CMPE", "integration_artifacts": ["cmpe_project_manifest.json", "cmpe_hub_genes.csv", "cmpe_hub_summary.md", "cmpe_figure_draft.md"], "next_action": "CMPE 통합 결과 과학 검토 후 별도 도킹 workflow handoff", "last_error": None, "updated_at_utc": now_utc()})
    write_json(project_path, project)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(integrate(args.project), ensure_ascii=False, indent=2))
