#!/usr/bin/env python3
"""Update recoverable NP checkpoint JSON and Markdown files."""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--computation-status", required=True)
    parser.add_argument("--save-status", required=True)
    parser.add_argument("--next-action", required=True)
    parser.add_argument("--primary-gene", action="append", default=[])
    parser.add_argument("--sensitivity-gene", action="append", default=[])
    parser.add_argument(
        "--branch-gene", action="append", default=[], metavar="BRANCH_ID=GENE",
        help="repeat for any registered branch; values are merged with legacy primary/sensitivity options",
    )
    parser.add_argument("--raw-result", action="append", default=[])
    parser.add_argument("--pending", action="append", default=[])
    parser.add_argument("--mapping-corrections")
    parser.add_argument("--job-ledger")
    parser.add_argument("--narrowing-audit")
    parser.add_argument("--stem", default="NP_checkpoint")
    args = parser.parse_args()

    root = args.run_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{args.stem}.json"
    data = {"history": []}
    if json_path.is_file():
        data = json.loads(json_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    branch_sets = defaultdict(set)
    branch_sets["primary"].update(args.primary_gene)
    branch_sets["sensitivity"].update(args.sensitivity_gene)
    for value in args.branch_gene:
        if "=" not in value:
            parser.error(f"--branch-gene must be BRANCH_ID=GENE: {value!r}")
        branch_id, gene = (part.strip() for part in value.split("=", 1))
        if not branch_id or not gene:
            parser.error(f"--branch-gene must contain nonblank branch and gene: {value!r}")
        branch_sets[branch_id].add(gene)
    branch_sets = {name: sorted(genes) for name, genes in sorted(branch_sets.items()) if genes}

    latest = {
        "updated_utc": now,
        "stage": args.stage,
        "computation_status": args.computation_status,
        "save_status": args.save_status,
        "primary_genes": branch_sets.get("primary", []),
        "sensitivity_genes": branch_sets.get("sensitivity", []),
        "branch_sets": branch_sets,
        "raw_results": args.raw_result,
        "mapping_corrections": args.mapping_corrections,
        "job_ledger": args.job_ledger,
        "narrowing_audit": args.narrowing_audit,
        "pending": args.pending,
        "next_action": args.next_action,
    }
    data.setdefault("history", []).append({
        "updated_utc": now,
        "stage": args.stage,
        "computation_status": args.computation_status,
        "save_status": args.save_status,
    })
    data["latest"] = latest
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# NP checkpoint", "", f"- Updated UTC: {now}", f"- Stage: {args.stage}",
        f"- Computation status: {args.computation_status}", f"- Save status: {args.save_status}",
        f"- Primary genes ({len(latest['primary_genes'])}): {', '.join(latest['primary_genes']) or 'not set'}",
        f"- Sensitivity genes ({len(latest['sensitivity_genes'])}): {', '.join(latest['sensitivity_genes']) or 'not set'}",
        "- Branch sets:",
    ]
    md.extend(
        f"  - {name} ({len(genes)}): {', '.join(genes)}"
        for name, genes in branch_sets.items()
    )
    if not branch_sets:
        md.append("  - none")
    md.extend([
        f"- Mapping corrections: {args.mapping_corrections or 'none recorded'}",
        f"- Job ledger: {args.job_ledger or 'not set'}",
        f"- Narrowing audit: {args.narrowing_audit or 'not set'}",
        f"- Raw results: {', '.join(args.raw_result) or 'not set'}",
        f"- Pending: {', '.join(args.pending) or 'none'}",
        f"- Next action: {args.next_action}", "",
    ])
    (root / f"{args.stem}.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(root / f'{args.stem}.md')}, indent=2))


if __name__ == "__main__":
    main()
