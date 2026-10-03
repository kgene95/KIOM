#!/usr/bin/env python3
import csv
import sys
from collections import defaultdict
from pathlib import Path


def norm(s):
    return " ".join((s or "").strip().split())


def main():
    if len(sys.argv) != 2:
        print("Usage: python check_consistency.py consistency_manifest.csv")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2
    groups = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"section", "item", "value", "source_location", "notes"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            print("Missing columns: " + ", ".join(sorted(missing)))
            return 2
        for row in reader:
            item = norm(row["item"]).lower()
            value = norm(row["value"])
            if item and value:
                groups[item].append(row)

    conflicts = 0
    for item, rows in sorted(groups.items()):
        values = defaultdict(list)
        for row in rows:
            values[norm(row["value"]).lower()].append(row)
        if len(values) > 1:
            conflicts += 1
            print(f"CONFLICT: {item}")
            for rows_for_value in values.values():
                display = norm(rows_for_value[0]["value"])
                locs = "; ".join(
                    f"{norm(r['section'])}: {norm(r['source_location'])}" for r in rows_for_value
                )
                print(f"  - {display} [{locs}]")
    if conflicts == 0:
        print("No conflicting repeated values detected.")
    else:
        print(f"Total conflict groups: {conflicts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
