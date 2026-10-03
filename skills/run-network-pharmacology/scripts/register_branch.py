#!/usr/bin/env python3
"""Add or replace one deterministic NP branch-registry row from an exact gene file."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


FIELDS = [
    "branch_id", "branch_class", "parent_branch", "purpose", "compound_rule",
    "disease_rule", "sources", "cutoffs", "species", "mapping_state",
    "gene_count", "exact_gene_file", "status", "permitted_interpretation", "created_utc",
]
CLASSES = ("primary", "sensitivity", "broad_exploratory", "proxy")
STATUSES = ("PENDING", "FAILED", "COMPLETED")


def read_genes(path, gene_column):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("exact gene file contains no rows")
    if gene_column not in rows[0]:
        raise ValueError(f"exact gene file lacks column {gene_column!r}")
    genes = {
        (row.get(gene_column) or "").strip().upper()
        for row in rows
        if (row.get(gene_column) or "").strip()
        and ("included" not in row or (row.get("included") or "").strip().casefold() in {"true", "1", "yes"})
    }
    if not genes:
        raise ValueError("exact gene file contains no included genes")
    return genes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("branch_id")
    parser.add_argument("branch_class", choices=CLASSES)
    parser.add_argument("exact_gene_file", help="path relative to run_dir")
    parser.add_argument("--gene-column", default="gene")
    parser.add_argument("--parent-branch", default="")
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--compound-rule", required=True)
    parser.add_argument("--disease-rule", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--cutoffs", required=True)
    parser.add_argument("--species", default="Homo sapiens")
    parser.add_argument("--mapping-state", required=True)
    parser.add_argument("--status", choices=STATUSES, default="COMPLETED")
    parser.add_argument("--permitted-interpretation", required=True)
    parser.add_argument("--created-utc")
    args = parser.parse_args()

    root = args.run_dir.resolve()
    exact_path = (root / args.exact_gene_file).resolve()
    try:
        exact_path.relative_to(root)
    except ValueError:
        parser.error("exact_gene_file must resolve inside run_dir")
    if not exact_path.is_file():
        parser.error(f"missing exact gene file: {args.exact_gene_file}")
    try:
        genes = read_genes(exact_path, args.gene_column)
    except ValueError as exc:
        parser.error(str(exc))

    registry = root / "branch_registry.csv"
    rows = []
    if registry.is_file():
        with registry.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        rows = [row for row in rows if (row.get("branch_id") or "").strip() != args.branch_id]

    rows.append({
        "branch_id": args.branch_id,
        "branch_class": args.branch_class,
        "parent_branch": args.parent_branch,
        "purpose": args.purpose,
        "compound_rule": args.compound_rule,
        "disease_rule": args.disease_rule,
        "sources": args.sources,
        "cutoffs": args.cutoffs,
        "species": args.species,
        "mapping_state": args.mapping_state,
        "gene_count": str(len(genes)),
        "exact_gene_file": args.exact_gene_file,
        "status": args.status,
        "permitted_interpretation": args.permitted_interpretation,
        "created_utc": args.created_utc or datetime.now(timezone.utc).isoformat(),
    })
    rows.sort(key=lambda row: row["branch_id"])
    registry.parent.mkdir(parents=True, exist_ok=True)
    with registry.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"registered {args.branch_id}: {len(genes)} genes -> {registry}")


if __name__ == "__main__":
    main()
