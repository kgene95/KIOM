from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main(run_text: str) -> int:
    run = Path(run_text)
    source = run / "compound_targets.csv"
    if not source.is_file():
        raise SystemExit(f"missing {source}")
    with source.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    identifiers = sorted({str(r.get("target_id", "")).strip() for r in rows if str(r.get("target_id", "")).strip() and str(r.get("target_id", "")).upper() != "NONE"})
    mapped: dict[str, dict[str, str]] = {}
    for start in range(0, len(identifiers), 40):
        chunk = identifiers[start:start + 40]
        clauses = []
        for ident in chunk:
            base = ident.removesuffix("_HUMAN")
            if re.fullmatch(r"[A-Z][0-9][A-Z0-9]{3}[0-9]|[A-Z0-9]{10}", base.upper()):
                clauses.append(f"accession:{base}")
            else:
                clauses.append(f"id:{base}_HUMAN")
        query = "(" + " OR ".join(clauses) + ") AND organism_id:9606 AND reviewed:true"
        url = "https://rest.uniprot.org/uniprotkb/search?" + urllib.parse.urlencode({"query": query, "format": "tsv", "fields": "accession,id,gene_names,organism_id,reviewed", "size": 500})
        req = urllib.request.Request(url, headers={"User-Agent": "KIOM-NP-harness-live-mapping/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            text = response.read().decode("utf-8")
        for item in csv.DictReader(text.splitlines(), delimiter="\t"):
            accession = item.get("Entry", "").strip()
            entry_name = item.get("Entry Name", "").strip()
            aliases = {accession.upper(), entry_name.upper(), entry_name.removesuffix("_HUMAN").upper()}
            aliases.update(x.upper() for x in item.get("Gene Names", "").split() if x)
            for alias in aliases:
                mapped[alias] = item
    out = run / "uniprot_live_mapping.csv"
    fields = ["submitted_id", "accession", "gene_names", "organism_id", "reviewed", "status"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for ident in identifiers:
            item = mapped.get(ident.upper()) or mapped.get((ident + "_HUMAN").upper())
            if item:
                w.writerow({"submitted_id": ident, "accession": item.get("Entry", ""), "gene_names": item.get("Gene Names", ""), "organism_id": item.get("Organism (ID)", ""), "reviewed": item.get("Reviewed", ""), "status": "LIVE_VERIFIED"})
            else:
                w.writerow({"submitted_id": ident, "status": "UNMAPPED"})
    statuses = list(csv.DictReader(out.open(newline="", encoding="utf-8")))
    verified = sum(r["status"] == "LIVE_VERIFIED" for r in statuses)
    manifest = {
        "resource": "UniProtKB REST API",
        "query_scope": "reviewed human proteins, taxonomy 9606",
        "source_file": str(source),
        "source_sha256": sha256(source),
        "output_file": str(out),
        "output_sha256": sha256(out),
        "queried_identifiers": len(identifiers),
        "live_verified": verified,
        "unmapped": len(statuses) - verified,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
    }
    (run / "uniprot_live_mapping_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0 if verified == len(statuses) else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
