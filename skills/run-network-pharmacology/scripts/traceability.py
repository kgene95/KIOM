"""Contract-v7 source/archive/lineage validation."""
import csv, hashlib, json, os
from pathlib import Path

def _hash(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _rows(root, name, problems):
    p=root/name
    if not p.is_file(): problems.append(f"missing: {name}"); return []
    with p.open(encoding="utf-8-sig", newline="") as h: return list(csv.DictReader(h))
def _inside(root, value):
    p=(root/value).resolve()
    try: p.relative_to(root.resolve()); return p
    except ValueError: return None
def validate_traceability(root, manifest):
    root=Path(root).resolve(); problems=[]
    attempts=_rows(root,"source_attempts.csv",problems); index=_rows(root,"source_archive_index.csv",problems); ledger=_rows(root,"data_adapter_ledger.csv",problems); lineage=_rows(root,"data_lineage.csv",problems)
    artifacts={}
    for r in index:
        aid=r.get("artifact_id",""); path=r.get("archive_path",""); p=_inside(root,path)
        if not aid or aid in artifacts: problems.append(f"duplicate artifact_id: {aid}")
        if not p or not str(path).replace('\\','/').startswith("source_archive/") or not p.is_file(): problems.append(f"missing archive: {path}")
        elif _hash(p)!=r.get("sha256"): problems.append(f"archive sha256 mismatch: {path}")
        artifacts[aid]=path
    seen=set()
    for r in attempts:
        key=tuple(r.get(k,"") for k in ("subject_type","subject_id","provider","source_role")); seen.add(key)
        if r.get("status") not in {"retrieved","not retrieved","unavailable","proxy","broad_exploratory"}: problems.append("invalid source attempt status")
        if r.get("retrieval_status") not in {"retrieved","not retrieved","unavailable"}: problems.append("invalid retrieval_status")
        if r.get("evidence_status") not in {"primary_eligible","proxy","broad_exploratory","not_assessed"}: problems.append("invalid evidence_status")
        if r.get("status")=="retrieved" and r.get("final_artifact_id") not in artifacts: problems.append("retrieved attempt lacks archive")
        if r.get("pagination_required"," ").lower()=="true" and (r.get("pagination_complete"," ").lower()!="true" or r.get("retrieval_complete"," ").lower()!="true" or not r.get("pagination_end_evidence")): problems.append("pagination is incomplete")
    for r in manifest.get("required_source_attempts",[]):
        key=tuple(r.get(k,"") for k in ("subject_type","subject_id","provider","source_role"))
        if key not in seen: problems.append(f"missing required source attempt: {key}")
    if manifest.get("used_adapters") and not ledger: problems.append("adapter retrieval has no ledger rows")
    outputs={}; graph={}
    for r in lineage:
        out=r.get("output_path",""); p=_inside(root,out)
        if out in outputs: problems.append(f"duplicate output_path: {out}")
        outputs[out]=r
        if not p or not p.is_file(): problems.append(f"lineage output missing: {out}")
        elif _hash(p)!=r.get("output_sha256"): problems.append(f"lineage output sha256 mismatch: {out}")
        try: ins=json.loads(r.get("input_paths","[]")); hs=json.loads(r.get("input_sha256","[]"))
        except json.JSONDecodeError: problems.append(f"invalid lineage arrays: {out}"); continue
        graph[out]=ins
        for i,h in zip(ins,hs):
            ip=_inside(root,i)
            valid=i.startswith("source_archive/") if out.startswith("raw/") else i.startswith(("raw/","normalized/"))
            if not valid or not ip or not ip.is_file(): problems.append(f"invalid lineage parent: {i}")
            elif _hash(ip)!=h: problems.append(f"lineage input sha256 mismatch: {i}")
        if r.get("transformation_type")=="manual":
            if r.get("transformation_script_sha256")!="NOT_APPLICABLE": problems.append("manual lineage has script hash")
        else:
            sp=_inside(root,r.get("transformation_script_path",""))
            if not sp or not sp.is_file() or _hash(sp)!=r.get("transformation_script_sha256"): problems.append("transformation script hash mismatch")
    def visit(n, stack):
        if n in stack: problems.append("lineage cycle"); return
        for x in graph.get(n,[]):
            if x in graph: visit(x, stack|{n})
    for n in graph: visit(n,set())
    return problems
