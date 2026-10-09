from __future__ import annotations
import csv, hashlib, json, re, shutil, io, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_VERSION = "1.0.0"

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def slug(s): return re.sub(r"[^A-Za-z0-9._-]+", "_", s.strip()).strip("._-")[:80] or "project"
def save_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"); tmp.replace(path)
def load_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def log(project: Path, msg: str):
    p=project/"logs/analysis_log.txt"; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f: f.write(f"[{now()}] {msg}\n")

def file_sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def create_project(root: Path, compound: dict | list[dict], disease: dict, mode: str, strategy: str = "current_de_novo"):
    root.mkdir(parents=True,exist_ok=True)
    compounds=compound if isinstance(compound,list) else [compound]
    if not compounds: raise ValueError("At least one confirmed compound is required.")
    primary_compound=compounds[0]
    name=f"{slug(primary_compound.get('name','compound'))}_{slug(disease.get('name','disease'))}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    p=root/name
    for d in ["00_project","01_np/raw/compound_targets","01_np/raw/disease_targets","01_np/processed","01_np/final","02_transcriptomics/raw","02_transcriptomics/processed","02_transcriptomics/final","03_cytoscape","logs","reports","export"]: (p/d).mkdir(parents=True,exist_ok=True)
    manifest={"app_version":APP_VERSION,"workflow":"run-network-pharmacology","created_utc":now(),"status":"PROJECT_CREATED","analysis_mode":mode,"analysis_strategy":strategy,"compound":primary_compound,"compounds":compounds,"disease":disease,"organism":{"name":"Homo sapiens","taxon_id":9606},"source_registry":[],"stages":{},"branches":{},"files":[],"limitations":[]}
    save_json(p/"00_project/NP_manifest.json",manifest)
    checkpoint={"stage":"PROJECT_CREATED","status":"PENDING","updated_utc":now(),"next_action":"Add source target evidence; validate IDs before interpreting overlap."}
    save_json(p/"00_project/NP_checkpoint.json",checkpoint)
    (p/"00_project/NP_checkpoint.md").write_text("# NP checkpoint\n\n- Stage: PROJECT_CREATED\n- Status: PENDING\n- NP completion: NOT_RUN\n- Transcriptomics: OPTIONAL_NOT_STARTED\n",encoding="utf-8")
    log(p,"Project created; no target analysis has run.")
    return p

def read_csv(path: Path):
    with path.open(newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def expand_source_upload(name: str, payload: bytes):
    """Decode CSV/TSV or a ZIP containing them without changing raw bytes."""
    def decode_one(filename, data):
        text = data.decode("utf-8-sig")
        delimiter = "\t" if filename.lower().endswith((".tsv", ".tab")) else ","
        rows = list(csv.DictReader(io.StringIO(text), delimiter=delimiter))
        return {"name": Path(filename).name, "raw_bytes": data, "rows": rows, "delimiter": delimiter}
    lower = name.lower()
    if lower.endswith(".zip"):
        out=[]
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for info in archive.infolist():
                if info.is_dir() or not info.filename.lower().endswith((".csv", ".tsv", ".tab")): continue
                out.append(decode_one(info.filename, archive.read(info)))
        if not out: raise ValueError(f"{name}: ZIP에 CSV/TSV 파일이 없습니다.")
        return out
    return [decode_one(name, payload)]

def normalized_upload_stem(upload_name: str, inner_name: str):
    """Return a collision-safe CSV stem for files extracted from an upload."""
    inner_stem=Path(inner_name).stem
    if upload_name.lower().endswith(".zip"):
        return f"{Path(upload_name).stem}_{inner_stem}"
    return inner_stem

def source_result_status(rows):
    """Classify an imported source without treating an empty official result as fatal."""
    return "IMPORTED" if rows else "EMPTY_RESULT"

def upload_provenance_status(source_url: str, retrieved_date: str, confirmed: bool):
    """Classify user-supplied provenance without claiming independent verification."""
    url = str(source_url or "").strip()
    date = str(retrieved_date or "").strip()
    if url and date and bool(confirmed):
        return {"status":"VERIFIED", "verification_method":"user_attested_url_and_date", "source_url":url, "retrieved_date":date}
    return {"status":"UNVERIFIED", "verification_method":"missing_url_date_or_confirmation", "source_url":url, "retrieved_date":date}

def write_csv(path: Path, rows: list[dict], fields=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=fields or (list(dict.fromkeys(k for row in rows for k in row)) if rows else [])
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def hub_metrics(nodes, edges):
    """Create a deterministic degree-based topology table from the frozen graph."""
    names={str(n.get("approved_symbol") or n.get("preferredName") or n.get("name") or "").strip() for n in nodes}
    names.discard("")
    degree={name:0 for name in names}; seen=set()
    for edge in edges:
        a=str(edge.get("preferredName_A") or edge.get("stringId_A") or edge.get("source") or "").strip()
        b=str(edge.get("preferredName_B") or edge.get("stringId_B") or edge.get("target") or "").strip()
        if not a or not b or a==b: continue
        pair=tuple(sorted((a,b)))
        if pair in seen: continue
        seen.add(pair)
        degree.setdefault(a,0); degree.setdefault(b,0); degree[a]+=1; degree[b]+=1
    rows=[{"approved_symbol":name,"degree":degree.get(name,0),"rank":0,"topology_source":"STRING graph; undirected unique edges; degree"} for name in degree]
    rows.sort(key=lambda row:(-row["degree"],row["approved_symbol"]))
    for index,row in enumerate(rows,1): row["rank"]=index
    return rows

def source_panel_gate(source_records, compound_rows_present, disease_rows_present):
    reasons=[]
    if not compound_rows_present: reasons.append("COMPOUND_TARGETS_MISSING")
    if not disease_rows_present: reasons.append("DISEASE_TARGETS_MISSING")
    if any(str(item.get("provenance_status","")).upper() in {"UNVERIFIED","MISSING"} for item in source_records):
        reasons.append("UNVERIFIED_SOURCE_PROVENANCE")
    return {"ready":not reasons,"reasons":reasons}

def target_column_present(rows):
    """Identify target evidence rows and reject auxiliary similarity tables."""
    if not rows:
        return False
    def keymap(row):
        return {re.sub(r"[^a-z0-9]", "", str(k).lower()) for k in row}
    accepted = {"target", "gene", "symbol", "uniprot", "uniprotid"}
    return any(keymap(row) & accepted for row in rows)

def validate_target_rows(rows, source_name):
    if not rows: raise ValueError(f"No records in {source_name}")
    def keymap(row):
        return {re.sub(r"[^a-z0-9]", "", str(k).lower()): k for k in row}
    def pick(row, *names):
        km=keymap(row)
        for name in names:
            if name in km: return row.get(km[name], "")
        return ""
    if not any(any(n in keymap(r) for n in ("target","gene","symbol","uniprot","uniprotid")) for r in rows):
        raise ValueError(f"{source_name}: expected target/gene/symbol/uniprot column")
    out=[]
    for r in rows:
        target=(pick(r,"target") or pick(r,"gene") or pick(r,"symbol") or pick(r,"uniprot") or pick(r,"uniprotid") or "").strip()
        species=(pick(r,"species") or pick(r,"organism") or pick(r,"taxid") or "").strip()
        species_ok=species.lower() in {"human","homo sapiens","9606","ncbitaxon:9606"}
        auto_human_gate=species == "AUTO_HUMAN_MAPPING_REQUIRED"
        out.append({**r,"target_submitted":target,"source":(r.get("source") or source_name).strip(),"species_submitted":species,"species_qc":"PASS_HUMAN" if species_ok else ("PENDING_HUMAN_MAPPING" if auto_human_gate else ("REVIEW_MISSING" if not species else "EXCLUDE_NONHUMAN")),"mapping_qc":"PENDING_STABLE_ID_MAPPING"})
    return out

def overlap_rows(compound_rows,disease_rows):
    def identifiers(r):
        vals=[]
        def add(v,prefix=""):
            if v:
                for part in re.split(r"[;,|\s]+",str(v)):
                    part=part.strip().upper()
                    if part: vals.append(prefix+part)
        add(r.get("approved_symbol") or r.get("target_submitted"))
        add(r.get("entrez_id"),"ENTREZ:")
        add(r.get("ensembl_id"),"ENSEMBL:")
        add(r.get("uniprot_accessions"),"UNIPROT:")
        add(r.get("uniprot_accession"),"UNIPROT:")
        return set(vals)
    def index(rows):
        d={}
        for r in rows:
            if r.get("species_qc")!="PASS_HUMAN": continue
            for ident in identifiers(r): d.setdefault(ident,[]).append(r)
        return d
    ci,di=index(compound_rows),index(disease_rows); out=[]; seen=set()
    for ident in sorted(ci.keys() & di.keys()):
        rows_c,rows_d=ci[ident],di[ident]
        symbol=next((x.get("approved_symbol") or x.get("target_submitted") for x in rows_c+rows_d if x.get("approved_symbol") or x.get("target_submitted")),ident)
        if symbol in seen: continue
        seen.add(symbol)
        out.append({"approved_symbol":symbol,"matched_identifier":ident,"compound_sources":";".join(sorted({x.get('source','') for x in rows_c})),"disease_sources":";".join(sorted({x.get('source','') for x in rows_d})),"compound_source_count":len({x.get('source','') for x in rows_c}),"disease_source_count":len({x.get('source','') for x in rows_d}),"branch":"broad_exploratory","mapping_qc":"PENDING_REVIEW"})
    return out

def analysis_review_findings(manifest: dict, required_files: list[str] | None = None):
    """Return explicit, user-facing warnings for incomplete NP evidence."""
    required_files = required_files or []
    counts = manifest.get("counts", {})
    findings = []
    if counts.get("overlap_genes", 0) and counts.get("string_nodes", 0) and not counts.get("string_edges", 0):
        findings.append({"code":"STRING_NO_EDGES", "severity":"warning", "message":"STRING ID 매핑은 되었지만 현재 기준에서 PPI edge가 0개입니다. hub/topology 네트워크를 해석할 수 없습니다."})
    if counts.get("overlap_genes", 0) and not counts.get("string_nodes", 0):
        findings.append({"code":"STRING_NO_NODES", "severity":"error", "message":"공통 표적은 있지만 STRING 노드 매핑이 없습니다."})
    provider_runs = {x.get("provider"): x for x in manifest.get("provider_runs", [])}
    if provider_runs.get("STRING enrichment", {}).get("terms", 0) == 0:
        findings.append({"code":"STRING_ENRICHMENT_EMPTY", "severity":"warning", "message":"STRING enrichment 결과가 0개입니다."})
    attempted = {str(x.get("source", "")).lower() for x in manifest.get("source_registry", [])}
    expected = {"pharmmapper", "swisstargetprediction", "sea", "pubchem", "stitch"}
    missing = sorted(x for x in expected if not any(x in a for a in attempted))
    if missing:
        findings.append({"code":"MISSING_SOURCE_PANEL", "severity":"warning", "message":"미수집 표적 자료원: " + ", ".join(missing)})
    unverified = [str(x.get("source", "")) for x in manifest.get("source_registry", []) if str(x.get("provenance_status", "")).upper() in {"UNVERIFIED", "MISSING"}]
    if unverified:
        findings.append({"code":"UNVERIFIED_SOURCE_PROVENANCE", "severity":"warning", "message":"출처 확인이 필요한 자료: " + ", ".join(sorted(unverified))})
    recorded_files = {str(x.get("path", "")).replace("\\", "/") for x in manifest.get("files", [])}
    missing_files = [f for f in required_files if f.replace("\\", "/") not in recorded_files]
    if missing_files:
        findings.append({"code":"MISSING_OUTPUT_FILES", "severity":"warning", "message":"필수 산출물 누락: " + ", ".join(missing_files)})
    if "STRING" in provider_runs and not any("hub" in str(x).lower() for x in manifest.get("files", [])):
        findings.append({"code":"HUB_ANALYSIS_NOT_GENERATED", "severity":"warning", "message":"hub/topology 순위표가 생성되지 않았습니다."})
    if not any("OmniPath" in str(x.get("provider", "")) for x in manifest.get("provider_runs", [])):
        findings.append({"code":"OMNIPATH_NOT_RUN", "severity":"info", "message":"OmniPath 조절·신호 주석은 아직 실행되지 않았습니다."})
    return findings

def write_cytoscape_exports(project:Path,nodes,edges):
    write_csv(project/"03_cytoscape/nodes.csv",nodes)
    write_csv(project/"03_cytoscape/edges.csv",edges)
    # GraphML XML without external graph dependencies
    import xml.etree.ElementTree as ET
    ns="http://graphml.graphdrawing.org/xmlns"; ET.register_namespace("",ns)
    graphml=ET.Element(f"{{{ns}}}graphml")
    ET.SubElement(graphml,f"{{{ns}}}key",id="score",**{"for":"edge","attr.name":"score","attr.type":"double"})
    g=ET.SubElement(graphml,f"{{{ns}}}graph",id="G",edgedefault="undirected")
    ids=set()
    for n in nodes:
        ident=n.get("string_id") or n.get("approved_symbol") or n.get("name")
        if ident and ident not in ids: ET.SubElement(g,f"{{{ns}}}node",id=str(ident)); ids.add(ident)
    for i,e in enumerate(edges):
        a=e.get("stringId_A") or e.get("preferredName_A"); b=e.get("stringId_B") or e.get("preferredName_B")
        if a in ids and b in ids:
            ee=ET.SubElement(g,f"{{{ns}}}edge",id=f"e{i}",source=str(a),target=str(b))
            try: ET.SubElement(ee,f"{{{ns}}}data",key="score").text=str(float(e.get("score",0)))
            except (TypeError,ValueError): pass
    ET.ElementTree(graphml).write(project/"03_cytoscape/network.graphml",encoding="utf-8",xml_declaration=True)
