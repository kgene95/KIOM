"""Read-only startup checks for the local KIOM NP Streamlit app."""
from __future__ import annotations

import importlib
import socket
import sys
from pathlib import Path


def check_runtime(root: Path, port: int = 8501) -> list[str]:
    errors: list[str] = []
    if sys.version_info < (3, 11):
        errors.append(f"Python 3.11+ is required; found {sys.version.split()[0]}")
    for module in ("streamlit", "requests", "pandas"):
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - depends on local install
            errors.append(f"Missing or broken dependency {module}: {type(exc).__name__}: {exc}")
    probe = root / ".kiom_preflight_write_test"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except Exception as exc:  # pragma: no cover - depends on local permissions
        errors.append(f"Project folder is not writable: {type(exc).__name__}: {exc}")
    with socket.socket() as sock:
        sock.settimeout(0.25)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            errors.append(f"Port {port} is already in use; close the existing Streamlit window first")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print(f"KIOM NP preflight | folder={root}")
    errors = check_runtime(root)
    if errors:
        print("PREFLIGHT FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PREFLIGHT OK | Python, dependencies, write access, and port 8501 are ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
