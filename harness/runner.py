"""Generic harness entrypoint.

Domain adapters own scientific task definitions. The generic runner owns the
durable lifecycle and delegates a cycle to the selected adapter.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="KIOM generic research harness")
    parser.add_argument("cycle", choices=["cycle"])
    parser.add_argument("--profile", required=True, help="domain adapter profile, e.g. np")
    parser.add_argument("--run", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-cycles", type=int, default=1)
    args = parser.parse_args()
    if args.profile != "np":
        raise SystemExit(f"등록되지 않은 profile: {args.profile}")
    sys.path.insert(0, str(Path(__file__).parent))
    from np_harness import cycle
    result = cycle(Path(args.run), dry_run=args.dry_run, max_cycles=args.max_cycles)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
