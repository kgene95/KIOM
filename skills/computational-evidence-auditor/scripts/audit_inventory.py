#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

NP_MANIFEST_FIELDS = [
    "species", "source_registry", "branch_lineage"
]
DOCK_MANIFEST_FIELDS = [
    "engine", "receptor", "ligand", "grid", "random_seed"
]


def nested_present(obj, key):
    if not isinstance(obj, dict):
        return False
    if key in obj and obj[key] not in (None, "", [], {}):
        return True
    return any(nested_present(v, key) for v in obj.values() if isinstance(v, dict))


def inspect_manifest(path, fields):
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"path": str(path), "parse_error": str(exc)}
    return {
        "path": str(path),
        "present_fields": [f for f in fields if nested_present(obj, f)],
        "missing_or_unrecognized_fields": [f for f in fields if not nested_present(obj, f)],
    }


def main():
    ap = argparse.ArgumentParser(description="Inventory NP/docking audit evidence without modifying inputs.")
    ap.add_argument("root", help="Directory containing an audit package")
    ap.add_argument("--output", default="audit_inventory.json")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    files = sorted(p for p in root.rglob("*") if p.is_file())
    ext_counts = {}
    for p in files:
        ext = p.suffix.lower() or "[no_ext]"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    names = {p.name.lower(): p for p in files}
    np_manifest = names.get("np_manifest.json")
    dock_manifest = names.get("docking_manifest.json")

    keywords = {
        "methods": ["method", "methods"],
        "results": ["result", "results"],
        "ppi": ["ppi", "string", "edge", "node"],
        "enrichment": ["go", "kegg", "reactome", "enrich"],
        "docking": ["dock", "vina", "pose", "rmsd", "interaction"],
        "figure": ["figure", "fig", "svg", "png", "tif", "tiff"],
    }
    categories = {}
    for cat, words in keywords.items():
        categories[cat] = [str(p.relative_to(root)) for p in files if any(w in p.name.lower() for w in words)]

    report = {
        "root": str(root),
        "file_count": len(files),
        "extension_counts": ext_counts,
        "categories": categories,
        "np_manifest": inspect_manifest(np_manifest, NP_MANIFEST_FIELDS) if np_manifest else {"status": "not_found"},
        "docking_manifest": inspect_manifest(dock_manifest, DOCK_MANIFEST_FIELDS) if dock_manifest else {"status": "not_found"},
        "note": "Field checks are structural hints only; scientific verification requires reading the underlying evidence."
    }

    out = root / args.output
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
