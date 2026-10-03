#!/usr/bin/env python3
"""Calculate optional within-source cutoff robustness matrices."""

import argparse
import csv
import json
from pathlib import Path


def read_rows(path):
    sep = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter=sep))


def cutoffs(value):
    return [float(item) for item in value.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", type=Path)
    parser.add_argument("disease", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--target-gene", default="gene")
    parser.add_argument("--target-score", default="score")
    parser.add_argument("--target-entity", default="compound")
    parser.add_argument("--target-source-column")
    parser.add_argument("--target-source-value")
    parser.add_argument("--target-include-column")
    parser.add_argument("--target-include-value", default="true")
    parser.add_argument("--disease-gene", default="gene")
    parser.add_argument("--disease-score", default="score")
    parser.add_argument("--disease-source-column")
    parser.add_argument("--disease-source-value")
    parser.add_argument("--disease-include-column")
    parser.add_argument("--disease-include-value", default="true")
    parser.add_argument("--target-cutoffs", required=True)
    parser.add_argument("--disease-cutoffs", required=True)
    args = parser.parse_args()

    target_rows = read_rows(args.targets)
    disease_rows = read_rows(args.disease)
    target_thresholds = cutoffs(args.target_cutoffs)
    disease_thresholds = cutoffs(args.disease_cutoffs)
    for rows, column, value, label in (
        (target_rows, args.target_source_column, args.target_source_value, "target"),
        (disease_rows, args.disease_source_column, args.disease_source_value, "disease"),
    ):
        if value and not column:
            parser.error(f"--{label}-source-value requires --{label}-source-column")
        if column:
            if rows and column not in rows[0]:
                parser.error(f"{label} input lacks source column {column!r}")
            available = sorted({row.get(column, "").strip() for row in rows if row.get(column, "").strip()})
            if value:
                rows[:] = [row for row in rows if row.get(column, "").strip() == value]
                if not rows:
                    parser.error(f"no {label} rows matched source {value!r}")
            elif len(available) > 1:
                parser.error(
                    f"multiple {label} sources have incomparable scores: {', '.join(available)}; "
                    f"supply --{label}-source-value"
                )
    if args.target_include_column:
        target_rows = [
            row for row in target_rows
            if row.get(args.target_include_column, "").strip().casefold()
            == args.target_include_value.strip().casefold()
        ]
    if args.disease_include_column:
        disease_rows = [
            row for row in disease_rows
            if row.get(args.disease_include_column, "").strip().casefold()
            == args.disease_include_value.strip().casefold()
        ]
    entities = sorted({row[args.target_entity].strip() for row in target_rows})
    matrix = []
    long_rows = []
    for target_cutoff in target_thresholds:
        entity_sets = {
            entity: {
                row[args.target_gene].strip()
                for row in target_rows
                if row[args.target_entity].strip() == entity
                and row[args.target_gene].strip()
                and float(row[args.target_score]) >= target_cutoff
            }
            for entity in entities
        }
        union = set().union(*entity_sets.values()) if entity_sets else set()
        for disease_cutoff in disease_thresholds:
            disease_set = {
                row[args.disease_gene].strip()
                for row in disease_rows
                if row[args.disease_gene].strip() and float(row[args.disease_score]) >= disease_cutoff
            }
            overlap = sorted(union & disease_set)
            result = {
                "target_cutoff": target_cutoff,
                "disease_cutoff": disease_cutoff,
                "target_union_count": len(union),
                "disease_count": len(disease_set),
                "overlap_count": len(overlap),
                "overlap_genes": ";".join(overlap),
            }
            for entity in entities:
                result[f"{entity}_target_count"] = len(entity_sets[entity])
                result[f"{entity}_overlap_count"] = len(entity_sets[entity] & disease_set)
            matrix.append(result)
            for gene in overlap:
                long_rows.append({
                    "target_cutoff": target_cutoff,
                    "disease_cutoff": disease_cutoff,
                    "gene": gene,
                    "compound_members": ";".join(e for e in entities if gene in entity_sets[e]),
                })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    matrix_fields = list(matrix[0]) if matrix else []
    with (args.output_dir / "sensitivity_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=matrix_fields)
        writer.writeheader()
        writer.writerows(matrix)
    with (args.output_dir / "sensitivity_overlap_long.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["target_cutoff", "disease_cutoff", "gene", "compound_members"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(long_rows)
    config = {
        "target_file": str(args.targets),
        "disease_file": str(args.disease),
        "target_columns": {
            "gene": args.target_gene,
            "score": args.target_score,
            "entity": args.target_entity,
            "include": args.target_include_column,
            "include_value": args.target_include_value if args.target_include_column else None,
            "source": args.target_source_column,
            "source_value": args.target_source_value,
        },
        "disease_columns": {
            "gene": args.disease_gene,
            "score": args.disease_score,
            "include": args.disease_include_column,
            "include_value": args.disease_include_value if args.disease_include_column else None,
            "source": args.disease_source_column,
            "source_value": args.disease_source_value,
        },
        "target_cutoffs": target_thresholds, "disease_cutoffs": disease_thresholds,
        "note": "Optional robustness analysis only. Use within one source whose native numeric score is comparable across rows.",
    }
    (args.output_dir / "sensitivity_config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"matrix_rows": len(matrix), "overlap_rows": len(long_rows)}, indent=2))


if __name__ == "__main__":
    main()
