"""실행 산출물과 해시를 독립적으로 확인하는 검증기."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifacts(run: Path) -> dict[str, Any]:
    manifest_path = run / "artifacts.json"
    if not manifest_path.exists():
        return {"status": "BLOCKED_NEEDS_USER", "reason": "artifacts.json 없음", "artifacts": []}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "CORRECT_AND_RERUN", "reason": f"manifest JSON 오류: {exc}", "artifacts": []}
    results = []
    for item in manifest.get("artifacts", []):
        path = run / item["path"]
        exists = path.is_file()
        actual = file_sha256(path) if exists else None
        expected = item.get("sha256")
        results.append({"path": item["path"], "exists": exists, "sha256": actual,
                        "sha256_match": expected is None or actual == expected})
    ok = bool(results) and all(row["exists"] and row["sha256_match"] for row in results)
    return {"status": "PASS" if ok else "CORRECT_AND_RERUN", "artifacts": results}


def verify_run_contract(run: Path) -> dict[str, Any]:
    required = ["request.json", "work_queue.json", "harness_state.json"]
    missing = [name for name in required if not (run / name).is_file()]
    return {"status": "PASS" if not missing else "BLOCKED_NEEDS_USER", "missing": missing}
