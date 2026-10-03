#!/usr/bin/env python3
"""Compute auditable gene-set overlaps from already curated target evidence."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="CSV: kind,entity,gene,source,source_id")
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    with args.input.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"kind", "entity", "gene", "source", "source_id"}
        if not required.issubset(reader.fieldnames or []):
            ap.error(f"required columns: {', '.join(sorted(required))}")
        rows = list(reader)
    if not rows:
        ap.error("input contains no evidence rows")
    sets = defaultdict(set)
    for line, row in enumerate(rows, 2):
        kind = row["kind"].strip().lower()
        if kind not in {"compound", "disease"}:
            ap.error(f"line {line}: kind must be compound or disease")
        if any(not row[col].strip() for col in required):
            ap.error(f"line {line}: required field blank")
        sets[(kind, row["entity"].strip())].add(row["gene"].strip())
    compounds = {entity: genes for (kind, entity), genes in sets.items() if kind == "compound"}
    diseases = {entity: genes for (kind, entity), genes in sets.items() if kind == "disease"}
    if not compounds or not diseases:
        ap.error("at least one compound and one disease set required")
    union = set().union(*compounds.values())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    counts = {"compound_counts": {k: len(v) for k, v in sorted(compounds.items())},
              "compound_union_count": len(union),
              "disease_counts": {k: len(v) for k, v in sorted(diseases.items())},
              "intersections": {}}
    with (args.output_dir / "overlap.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["disease", "gene", "compound_members"])
        for disease, genes in sorted(diseases.items()):
            common = union & genes
            counts["intersections"][disease] = {"union": len(common),
                "per_compound": {k: len(v & genes) for k, v in sorted(compounds.items())}}
            for gene in sorted(common):
                writer.writerow([disease, gene, ";".join(sorted(k for k, v in compounds.items() if gene in v))])
    (args.output_dir / "counts.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
