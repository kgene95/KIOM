#!/usr/bin/env python3
"""Merge a scientific seed manifest with deterministic file and script hashes."""

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("seed", type=Path, help="JSON containing scientific rules and sets")
    parser.add_argument("output", type=Path)
    parser.add_argument("--include-file", action="append", default=[])
    parser.add_argument("--script", action="append", default=[])
    args = parser.parse_args()

    root = args.run_dir.resolve()
    manifest = json.loads(args.seed.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    manifest["manifest_generated_utc"] = now
    if manifest.get("status") == "NP_COMPLETE_DOCKING_NOT_STARTED":
        manifest.setdefault("analysis_completed_utc", now)
    manifest["runtime"] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }
    try:
        contract_version = int(manifest.get("contract_version", 0))
    except (TypeError, ValueError):
        parser.error("contract_version must be an integer")
    if contract_version >= 5:
        required = (
            "analysis_started_utc", "analysis_completed_utc", "software_inventory",
            "database_inventory", "analysis_parameters",
        )
        missing = [name for name in required if not manifest.get(name)]
        if missing:
            parser.error(f"contract v5 seed missing metadata: {', '.join(missing)}")
    manifest["file_inventory"] = []
    for relative in args.include_file:
        path = (root / relative).resolve()
        if not path.is_file():
            parser.error(f"missing file: {relative}")
        manifest["file_inventory"].append({
            "path": relative, "bytes": path.stat().st_size, "sha256": digest(path)
        })
    manifest["script_inventory"] = []
    for value in args.script:
        path = Path(value).resolve()
        if not path.is_file():
            parser.error(f"missing script: {value}")
        manifest["script_inventory"].append({
            "path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(manifest["file_inventory"]), "scripts": len(manifest["script_inventory"])}, indent=2))


if __name__ == "__main__":
    main()
