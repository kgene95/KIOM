#!/usr/bin/env python3
"""Add or replace one auditable broad-to-final narrowing decision."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


FIELDS = [
    "step_id", "parent_set", "new_set", "changed_rule", "source",
    "threshold_or_rule", "before_count", "after_count", "overlap_before",
    "overlap_after", "ppi_nodes_before", "ppi_nodes_after", "ppi_edges_before",
    "ppi_edges_after", "gained_genes", "lost_genes", "enrichment_change",
    "hub_change", "reason", "decision", "created_utc",
]


def read_genes(path, column):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path.name} contains no rows")
    if column not in rows[0]:
        raise ValueError(f"{path.name} lacks gene column {column!r}")
    return {
        (row.get(column) or "").strip().upper()
        for row in rows
        if (row.get(column) or "").strip()
        and ("included" not in row or (row.get("included") or "").strip().casefold() in {"true", "1", "yes"})
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("step_id")
    parser.add_argument("parent_set")
    parser.add_argument("new_set")
    parser.add_argument("parent_gene_file")
    parser.add_argument("new_gene_file")
    parser.add_argument("--gene-column", default="gene")
    parser.add_argument("--changed-rule", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--threshold-or-rule", required=True)
    parser.add_argument("--before-count", required=True, type=int)
    parser.add_argument("--after-count", required=True, type=int)
    parser.add_argument("--ppi-nodes-before", required=True)
    parser.add_argument("--ppi-nodes-after", required=True)
    parser.add_argument("--ppi-edges-before", required=True)
    parser.add_argument("--ppi-edges-after", required=True)
    parser.add_argument("--enrichment-change", required=True)
    parser.add_argument("--hub-change", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--decision", required=True)
    parser.add_argument("--created-utc")
    args = parser.parse_args()

    root = args.run_dir.resolve()
    parent_path = (root / args.parent_gene_file).resolve()
    new_path = (root / args.new_gene_file).resolve()
    for path in (parent_path, new_path):
        try:
            path.relative_to(root)
        except ValueError:
            parser.error("gene files must resolve inside run_dir")
        if not path.is_file():
            parser.error(f"missing gene file: {path}")
    try:
        before_genes = read_genes(parent_path, args.gene_column)
        after_genes = read_genes(new_path, args.gene_column)
    except ValueError as exc:
        parser.error(str(exc))

    row = {
        "step_id": args.step_id,
        "parent_set": args.parent_set,
        "new_set": args.new_set,
        "changed_rule": args.changed_rule,
        "source": args.source,
        "threshold_or_rule": args.threshold_or_rule,
        "before_count": str(args.before_count),
        "after_count": str(args.after_count),
        "overlap_before": str(len(before_genes)),
        "overlap_after": str(len(after_genes)),
        "ppi_nodes_before": args.ppi_nodes_before,
        "ppi_nodes_after": args.ppi_nodes_after,
        "ppi_edges_before": args.ppi_edges_before,
        "ppi_edges_after": args.ppi_edges_after,
        "gained_genes": ";".join(sorted(after_genes - before_genes)),
        "lost_genes": ";".join(sorted(before_genes - after_genes)),
        "enrichment_change": args.enrichment_change,
        "hub_change": args.hub_change,
        "reason": args.reason,
        "decision": args.decision,
        "created_utc": args.created_utc or datetime.now(timezone.utc).isoformat(),
    }

    output = root / "narrowing_audit.csv"
    rows = []
    if output.is_file():
        with output.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        rows = [existing for existing in rows if (existing.get("step_id") or "").strip() != args.step_id]
    rows.append(row)
    rows.sort(key=lambda item: item["step_id"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"recorded {args.step_id}: overlap {len(before_genes)} -> {len(after_genes)}; "
        f"gained {len(after_genes - before_genes)}, lost {len(before_genes - after_genes)}"
    )


if __name__ == "__main__":
    main()
