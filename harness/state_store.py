"""영속 실행 상태와 이벤트를 안전하게 기록하는 범용 저장소."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def append_event(run: Path, event: dict[str, Any]) -> None:
    path = run / "event_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"at_utc": now_utc(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_state(run: Path, **changes: Any) -> dict[str, Any]:
    path = run / "harness_state.json"
    state = load_json(path, {"run_id": run.name, "status": "RUNNING", "attempts": 0})
    state.update(changes)
    state["last_updated_utc"] = now_utc()
    save_json_atomic(path, state)
    return state
