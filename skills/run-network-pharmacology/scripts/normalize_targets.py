#!/usr/bin/env python3
"""Normalize, species-filter, merge, and deduplicate compatible target tables."""

import argparse
import csv
import json
from pathlib import Path


def delimiter(path):
    return "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","


def clean(value):
    return " ".join(str(value or "").strip().split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--gene-column", required=True)
    parser.add_argument("--species-column")
    parser.add_argument("--allowed-species", action="append", default=[])
    parser.add_argument("--stable-id-column")
    parser.add_argument("--entity-column")
    parser.add_argument("--source-column")
    parser.add_argument("--uppercase-gene", action="store_true")
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    allowed = {clean(value).casefold() for value in args.allowed_species}
    rows = []
    field_order = []
    for source_index, path in enumerate(args.inputs):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter(path))
            if args.gene_column not in (reader.fieldnames or []):
                parser.error(f"{path}: missing gene column {args.gene_column!r}")
            for field in reader.fieldnames or []:
                if field not in field_order:
                    field_order.append(field)
            for row_index, raw in enumerate(reader, 2):
                row = {key: clean(value) for key, value in raw.items()}
                gene = row.get(args.gene_column, "")
                if args.uppercase_gene:
                    gene = gene.upper()
                row["normalized_gene"] = gene
                row["source_file"] = path.name
                row["source_file_order"] = str(source_index)
                row["source_row"] = str(row_index)
                rows.append(row)

    seen = set()
    counts = {"input_rows": len(rows), "included": 0, "missing_gene": 0, "species_excluded": 0, "duplicate": 0}
    for row in rows:
        reason = ""
        gene = row["normalized_gene"]
        if not gene:
            reason = "missing_gene"
        elif args.species_column and allowed and row.get(args.species_column, "").casefold() not in allowed:
            reason = "species_excluded"
        entity = row.get(args.entity_column, "") if args.entity_column else ""
        stable_id = row.get(args.stable_id_column, "") if args.stable_id_column else ""
        source = row.get(args.source_column, "") if args.source_column else row["source_file"]
        key = (entity, gene, stable_id, source)
        if not reason and key in seen:
            reason = "duplicate"
        if not reason:
            seen.add(key)
            counts["included"] += 1
            row["included"] = "true"
        else:
            counts[reason] += 1
            row["included"] = "false"
        row["exclusion_reason"] = reason

    output_fields = list(dict.fromkeys(field_order + [
        "normalized_gene", "source_file", "source_file_order", "source_row",
        "included", "exclusion_reason",
    ]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary_path = args.summary or args.output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
