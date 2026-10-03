#!/usr/bin/env python3
"""Compare submitted, mapped, expected identifiers and species deterministically."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def delimiter(path):
    return "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","


def norm(value):
    return " ".join(str(value or "").strip().split()).upper()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--submitted", default="submitted_gene")
    parser.add_argument("--mapped", default="mapped_gene")
    parser.add_argument("--expected", default="expected_gene")
    parser.add_argument("--species", default="species")
    parser.add_argument("--expected-species", default="expected_species")
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter(args.input))
        required = [args.submitted, args.mapped, args.expected, args.species, args.expected_species]
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            parser.error(f"missing columns: {', '.join(sorted(missing))}")
        input_fields = list(reader.fieldnames or [])
        rows = list(reader)

    counts = Counter()
    for row in rows:
        submitted = norm(row[args.submitted])
        mapped = norm(row[args.mapped])
        expected = norm(row[args.expected]) or submitted
        species = norm(row[args.species])
        expected_species = norm(row[args.expected_species])
        if not mapped:
            status, reason = "UNMAPPED", "mapped identifier missing"
        elif expected_species and species != expected_species:
            status, reason = "SPECIES_MISMATCH", f"{species} != {expected_species}"
        elif mapped != expected:
            status, reason = "IDENTITY_MISMATCH", f"{mapped} != {expected}"
        else:
            status, reason = "PASS", ""
        row["qc_status"] = status
        row["included"] = "true" if status == "PASS" else "false"
        row["qc_reason"] = reason
        counts[status] += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(input_fields + ["qc_status", "included", "qc_reason"]))
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = {"rows": len(rows), "statuses": dict(sorted(counts.items()))}
    (args.summary or args.output.with_suffix(".summary.json")).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
