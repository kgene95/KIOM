#!/usr/bin/env python3
"""Validate a data-derived eight-panel SCI network-pharmacology figure package."""

import argparse
import csv
import json
from pathlib import Path


PANELS = "ABCDEFGH"
FILE_SUFFIXES = {
    "A": "compound_target_network.svg",
    "B": "target_acquisition_disease_set.svg",
    "C": "overlap_venn.svg",
    "D": "PPI_network.svg",
    "E": "hub_gene_ranking.svg",
    "F": "hub_subnetwork.svg",
    "G": "GO_integrated.svg",
    "H": "KEGG_enrichment.svg",
}
PANEL_FIELDS = {
    "panel", "analysis_name", "input_files", "branch_id", "exact_gene_set_file",
    "data_transformation", "encoding", "exclusions", "fdr_rule", "layout_seed",
    "scientific_limitation",
}
ENCODING_FIELDS = {"x", "y", "node", "color", "size"}
QA_FIELDS = {"panel", "check", "expected", "observed", "source", "status"}
REQUIRED_QA_CHECKS = {
    "A": "target_count_and_edges",
    "B": "sources_filters_counts_species_branch",
    "C": "overlap_counts_and_exact_set",
    "D": "ppi_mapping_nodes_edges_isolates",
    "E": "hub_genes_rank_metric_score",
    "F": "hub_nodes_and_edge_subset",
    "G": "go_terms_statistics_members",
    "H": "pathway_ratio_statistics_members",
}


def safe_file(base, relative, label, problems):
    if not isinstance(relative, str) or not relative.strip():
        problems.append(f"{label}: missing path")
        return None
    path = (base / relative).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        problems.append(f"{label}: path escapes base directory: {relative}")
        return None
    if not path.is_file() or path.stat().st_size == 0:
        problems.append(f"{label}: missing or empty: {relative}")
    return path


def read_branch_ids(run_dir, problems):
    path = run_dir / "branch_registry.csv"
    if not path.is_file():
        problems.append("missing branch_registry.csv")
        return set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return {(row.get("branch_id") or "").strip() for row in rows if (row.get("branch_id") or "").strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("figure_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    figure_dir = args.figure_dir.resolve()
    problems = []

    spec_path = figure_dir / "visual_spec.json"
    if not spec_path.is_file():
        problems.append("missing visual_spec.json")
        spec = {}
    else:
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            problems.append(f"invalid visual_spec.json: {exc}")
            spec = {}

    branches = read_branch_ids(run_dir, problems)
    status = str(spec.get("status") or "").strip()
    if status not in {"REVIEW_DRAFT", "SCI-final"}:
        problems.append("visual_spec status must be REVIEW_DRAFT or SCI-final")
    is_final = status == "SCI-final"
    figure_number = str(spec.get("figure_number") or "").strip()
    if not figure_number:
        problems.append("visual_spec missing figure_number")
        figure_token = "Fig"
    else:
        digits = "".join(character for character in figure_number if character.isdigit())
        figure_token = f"Fig{digits}" if digits else "Fig"

    panels = spec.get("panels")
    if not isinstance(panels, list):
        problems.append("visual_spec panels must be a list")
        panels = []
    panel_map = {}
    for item in panels:
        if not isinstance(item, dict):
            problems.append("panel entry must be an object")
            continue
        panel = str(item.get("panel") or "").strip().upper()
        if panel in panel_map:
            problems.append(f"duplicate panel: {panel}")
        panel_map[panel] = item
        missing = PANEL_FIELDS - set(item)
        if missing:
            problems.append(f"panel {panel or '?'} missing fields: {', '.join(sorted(missing))}")
        if item.get("branch_id") not in branches:
            problems.append(f"panel {panel}: unregistered branch {item.get('branch_id')!r}")
        safe_file(run_dir, item.get("exact_gene_set_file"), f"panel {panel} exact gene set", problems)
        inputs = item.get("input_files")
        if not isinstance(inputs, list) or not inputs:
            problems.append(f"panel {panel}: input_files must be a nonempty list")
        else:
            for relative in inputs:
                safe_file(run_dir, relative, f"panel {panel} input", problems)
        encoding = item.get("encoding")
        if not isinstance(encoding, dict) or ENCODING_FIELDS - set(encoding):
            problems.append(f"panel {panel}: encoding must contain x,y,node,color,size")
        expected_output = f"{figure_token}{panel}_{FILE_SUFFIXES[panel]}" if panel in FILE_SUFFIXES else None
        output_file = item.get("output_file")
        if is_final:
            if expected_output and output_file != expected_output:
                problems.append(f"panel {panel}: output_file must be {expected_output}")
            safe_file(figure_dir, output_file, f"panel {panel} output", problems)
        elif output_file not in {None, ""}:
            problems.append(f"panel {panel}: REVIEW_DRAFT must not export an individual output_file")
        elif expected_output and (figure_dir / expected_output).exists():
            problems.append(f"panel {panel}: individual panel exists before approval: {expected_output}")

    if set(panel_map) != set(PANELS):
        problems.append("visual_spec must contain exactly panels A-H")

    composites = spec.get("composite_files")
    if not isinstance(composites, list) or not composites:
        problems.append("visual_spec composite_files must be a nonempty list")
        composites = []
    suffixes = set()
    for relative in composites:
        path = safe_file(figure_dir, relative, "composite", problems)
        if path:
            suffixes.add(path.suffix.lower())
    if is_final:
        if ".svg" not in suffixes or ".pdf" not in suffixes or not ({".png", ".tif", ".tiff"} & suffixes):
            problems.append("SCI-final composite_files must include SVG, PDF, and PNG/TIFF")
        if str(spec.get("user_approval_status") or "").strip().upper() != "APPROVED":
            problems.append("SCI-final requires user_approval_status: APPROVED")
        if not str(spec.get("user_approval_recorded_utc") or "").strip():
            problems.append("SCI-final requires user_approval_recorded_utc")
    elif not ({".svg", ".pdf", ".png", ".tif", ".tiff"} & suffixes):
        problems.append("REVIEW_DRAFT requires at least one composite SVG/PDF/PNG/TIFF")

    safe_file(figure_dir, spec.get("plotting_source"), "plotting source", problems)
    if is_final:
        safe_file(figure_dir, spec.get("caption_file"), "caption", problems)
    qa_relative = spec.get("qa_file")
    qa_path = safe_file(figure_dir, qa_relative, "figure QA", problems)
    if qa_path and qa_path.is_file():
        with qa_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            problems.append("figure_qa.csv has no checks")
        elif QA_FIELDS - set(rows[0]):
            problems.append(f"figure_qa.csv missing columns: {', '.join(sorted(QA_FIELDS - set(rows[0])))}")
        qa_panels = {(row.get("panel") or "").strip().upper() for row in rows}
        if not set(PANELS).issubset(qa_panels):
            problems.append("figure_qa.csv must include every panel A-H")
        qa_pairs = {
            ((row.get("panel") or "").strip().upper(), (row.get("check") or "").strip())
            for row in rows
        }
        for panel, check in REQUIRED_QA_CHECKS.items():
            if (panel, check) not in qa_pairs:
                problems.append(f"figure_qa.csv missing required check for panel {panel}: {check}")
        for index, row in enumerate(rows, 2):
            if (row.get("status") or "").strip().upper() != "PASS":
                problems.append(f"figure_qa.csv line {index}: status is not PASS")

    if problems:
        for problem in problems:
            print(problem)
        raise SystemExit(1)
    label = "SCI-final figure package" if is_final else "composite review figure"
    print(f"{label} valid: {figure_dir}")


if __name__ == "__main__":
    main()
