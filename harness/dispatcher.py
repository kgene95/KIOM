"""등록된 worker만 호출하는 안전한 dispatcher."""
from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dispatch_registered_worker(run: Path, task: dict[str, Any], registry_path: Path, *, approved: bool = False) -> dict[str, Any]:
    name = task.get("worker")
    registry = load_registry(registry_path).get("workers", {})
    spec = registry.get(name)
    if not spec:
        return {"status": "FAILED", "reason": f"등록되지 않은 worker: {name}"}
    if spec.get("requires_approval") and not approved:
        return {"status": "WAITING_USER", "reason": "worker 승인 필요"}
    scripts = registry_path.parents[1] / "skills" / "run-network-pharmacology" / "scripts"
    sys.path.insert(0, str(scripts))
    sys.path.insert(0, str(registry_path.parent))
    module = importlib.import_module(spec["module"])
    function = getattr(module, spec["function"])
    if len(inspect.signature(function).parameters) == 1:
        result = function(run)
    else:
        result = function(run, task.get("id"))
    return {"status": "DONE", "worker": name, "result": result}
