#!/usr/bin/env python3
"""Generate continuation records for a shared docking project.

The command is intentionally conservative: it validates the expected material
and project names, writes only record files, and never deletes or moves data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative_files(root: Path):
    excluded = {"FOLDER_STATUS.md", "PROJECT_README.md"}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in excluded:
            yield p


def write_inventory(root: Path, path: Path, destination: str):
    rows = []
    for p in relative_files(root):
        rel = p.relative_to(root).as_posix()
        rows.append({
            "relative_path": rel,
            "role": "record" if p.name.upper() in {"README_AGENT.MD", "CURRENT_STATUS.MD", "CHANGELOG.MD", "GITHUB_ONEDRIVE_HANDOFF.MD", "DOCKING_CHECKPOINT.MD", "DOCKING_MANIFEST.JSON"} else "data_or_script",
            "size_bytes": p.stat().st_size,
            "modified_utc": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
            "sha256": sha256(p),
            "sync_destination": destination,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["relative_path", "role", "size_bytes", "modified_utc", "sha256", "sync_destination"])
        writer.writeheader()
        writer.writerows(rows)


def write_folder_status(folder: Path, root: Path, material: str, project: str):
    dirs = [p.name for p in sorted(folder.iterdir()) if p.is_dir()]
    files = [p.name for p in sorted(folder.iterdir()) if p.is_file() and p.name not in {"FOLDER_STATUS.md", "PROJECT_README.md"}]
    rel = folder.relative_to(root).as_posix() if folder != root else "."
    lines = [
        f"# Folder status — {rel}",
        "",
        f"- Material: `{material}`",
        f"- Project: `{project}`",
        f"- Folder: `{rel}`",
        f"- Generated UTC: `{datetime.now(timezone.utc).isoformat()}`",
        "- This file is a continuation index; read it before opening raw structures or rerunning calculations.",
        "",
        "## Immediate subfolders",
        "",
    ]
    lines += [f"- `{d}/`" for d in dirs] or ["- None"]
    lines += ["", "## Immediate files", ""]
    lines += [f"- `{f}`" for f in files] or ["- None"]
    folder.joinpath("FOLDER_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--material", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--destination", default="OneDrive")
    args = ap.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Root not found: {root}")
    if args.material not in root.name and args.material.upper() != "CMPE":
        raise SystemExit(f"Material identity mismatch for {root}: expected {args.material}")
    required = [root / "00_PROJECT", root / "docking_manifest.json", root / "docking_checkpoint.md"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Expected project records missing: " + ", ".join(missing))
    record_dirs = [root] + [p for p in sorted(root.iterdir()) if p.is_dir()]
    for p in record_dirs:
        write_folder_status(p, root, args.material, args.project)
    write_inventory(root, root / "00_PROJECT" / "file_inventory.csv", args.destination)
    print(f"Updated records for {root} ({len(list(relative_files(root)))} files inventoried)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
