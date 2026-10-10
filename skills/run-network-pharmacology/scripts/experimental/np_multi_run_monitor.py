from pathlib import Path
import argparse,datetime,hashlib,json,os,csv,re,urllib.request,urllib.error,time
from urllib.parse import urlparse
ROOT=Path(r"D:\GPT-CODECX\KIOM_NP_Projects")
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p,d=None):
 try:return json.loads(Path(p).read_text(encoding="utf-8"))
 except (FileNotFoundError,ValueError):return {} if d is None else d
def save(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp")
 tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8");os.replace(tmp,p)
def digest(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def candidates(run):
 req=read(run/"request.json");identity=read(run/"structure_manifest.json")
 rawname=req.get("compound_input","").strip()
 cid=str(identity.get("cid") or "")
 if not cid:
  m=re.search(r"(?:CID\s*[:#]?)?(\d{4,10})",rawname,re.I)
  cid=m.group(1) if m else ""
 name=rawname.lower()
 aliases={name,("cid"+cid).lower(),cid}
 aliases={x for x in aliases if len(x)>=4}
 hits=[]
 # Includes previous runs and source folders but never trusts a filename alone.
 for folder in ROOT.iterdir():
  if not folder.is_dir() or folder==run.parent.parent:continue
  inspected=0
  for f in folder.rglob("*"):
   if inspected>7000:break
   inspected+=1
   if not f.is_file() or f.suffix.lower() not in (".tsv",".csv",".sdf",".mol2",".json",".html"):continue
   if "background_monitor" in f.parts or "integrated_sensitivity" in f.parts:continue
   if f.stat().st_size>5_000_000:continue
   namehit=any(alias in str(f).lower() for alias in aliases)
   contenthit=False;provenance={}
   if f.suffix.lower()==".json":
    try:
     val=json.loads(f.read_text(encoding="utf-8"))
     if isinstance(val,dict):
      filecid=str(val.get("pubchem_cid") or val.get("cid") or val.get("compound_cid") or "")
      contenthit=bool(cid and filecid==cid)
      provenance=val
    except (UnicodeError,ValueError):pass
   elif f.suffix.lower() in (".tsv",".csv",".html") and f.stat().st_size<300000:
    try:
     text=f.read_text(encoding="utf-8-sig",errors="replace")[:15000].lower()
     contenthit=any(a in text for a in aliases)
    except OSError:pass
   if not namehit and not contenthit:continue
   try:
    h=digest(f)
    required=["job_id","species","analysis_parameters","retrieved_at_utc"]
    source=("SEA" if "sea_" in f.name.lower() else "PharmMapper" if "pharmmapper" in str(f).lower() else "OTHER")
    evidence=read(run/"verification_evidence.json").get(h,{})
    validated=bool(cid and evidence.get("cid")==cid and evidence.get("species")==req.get("species") and
      evidence.get("raw_sha256")==h and evidence.get("job_id") and
      evidence.get("structure_sha256")==identity.get("structure_sha256") and
      evidence.get("analysis_parameters") and evidence.get("reviewer_verified") is True)
    proof="verification_evidence.json:"+h if validated else ("METADATA_AVAILABLE_REVIEW" if contenthit else "NOT_AVAILABLE")
    hits.append({"source_file":str(f),"sha256":h,"bytes":f.stat().st_size,"source":source,
      "match":"COMPOUND_AND_METHOD_VERIFIED" if validated else "CONTENT_CID_REVIEW" if contenthit else "FILENAME_ONLY_UNVERIFIED",
      "proof":proof,"decision":"PENDING",
      "missing_checks":[] if validated else [k for k in required if not provenance.get(k)]})
   except OSError:continue
 return hits[:150]

def review(run):
 run=Path(run);old=read(run/"existing_data_review.json")
 items=candidates(run)
 bypath={a["source_file"]:a for a in old.get("candidates",[])}
 for v in items:
  prev=bypath.get(v["source_file"])
  if prev and prev.get("sha256")==v["sha256"]:
   # Never restore outdated verification; only preserve user decision if gate still passes.
   decision=prev.get("decision","PENDING")
   if decision=="REUSE_VERIFIED" and v["match"]!="COMPOUND_AND_METHOD_VERIFIED":
    v["decision"]="PENDING"
   else:v["decision"]=decision
   if "approval_time_utc" in prev:v["approval_time_utc"]=prev["approval_time_utc"]
 report={"run_id":read(run/"request.json").get("run_id"),"generated_at":now(),"priority":"EXISTING_DATA_FIRST","candidates":items,"requires_explicit_approval":bool(items),"supplement_prompt":"검증이 부족한 자료는 보완 분석을 진행할까요?","default_action":"STOP_AND_REVIEW" if items else "CONTINUE_SOURCE_AUDIT","notes":"파일명은 동일 화합물의 증거가 아닙니다. 실제 CID/SMILES·종·작업 ID·조건을 대조해야 재사용할 수 있습니다."}
 save(run/"existing_data_review.json",report)
 return report
def decision(run,item_sha,action,proof):
 run=Path(run);r=read(run/"existing_data_review.json");allowed={"REUSE_VERIFIED","REANALYZE","SUPPLEMENT","EXCLUDE"}
 if action not in allowed:raise ValueError("유효하지 않은 승인")
 updated=False
 for c in r.get("candidates",[]):
  if c["sha256"]==item_sha:
   if action=="REUSE_VERIFIED" and (c.get("match")!="COMPOUND_AND_METHOD_VERIFIED" or not c.get("proof") or c["proof"]=="NOT_AVAILABLE"):
    raise ValueError("화합물·분석조건의 출처 검증 완료 전에는 재사용 불가")
   c["decision"]=action;c["approval_time_utc"]=now();c["approval_evidence"]=proof or "USER_APPROVAL"
   updated=True;break
 if not updated:raise ValueError("대상 파일을 찾지 못했습니다.")
 save(run/"existing_data_review.json",r)
 return {"saved":True,"action":action}
def poll_pharmmapper(run):
 run=Path(run);ledger=read(run/"job_ledger.json");summary=[]
 for key,row in ledger.items():
  if row.get("provider")!="PharmMapper" or row.get("status") not in ("SUBMITTED","PENDING"):continue
  jobid=str(row.get("job_id",""))
  if not re.fullmatch(r"\d{12}",jobid):continue
  url="https://www.lilab-ecust.cn/pharmmapper/results/"+jobid+".html"
  try:
   response=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=15)
   raw=response.read(6_000_000);html=raw.decode("utf-8","replace")
   if "Job is expired" in html:row["status"]="EXPIRED";status="EXPIRED"
   elif "Transmition progress" in html or "Invalid request" in html:status="PENDING"
   elif "Results Downloading" in html and len(raw)>5000:
    out=run/"source_archive"/"PharmMapper";out.mkdir(parents=True,exist_ok=True)
    dest=out/(jobid+"_"+hashlib.sha256(raw).hexdigest()[:12]+".html")
    if not dest.exists():dest.write_bytes(raw)
    row["raw_file"]=str(dest);row["sha256"]=digest(dest);row["status"]="RETRIEVED_UNVERIFIED";status="RETRIEVED_UNVERIFIED"
   else:status="PENDING"
   row["last_checked_utc"]=now();summary.append({"job_id":jobid,"state":status})
  except Exception as e:summary.append({"job_id":jobid,"state":"NETWORK_ERROR","detail":str(e)[:130]})
 save(run/"job_ledger.json",ledger)
 return summary
def poll_sea(run):
 ledger=read(Path(run)/"job_ledger.json");summary=[]
 for key,row in ledger.items():
  if row.get("provider")!="SEA" or row.get("status") not in ("SUBMITTED","PENDING"):continue
  # SEA endpoint is not assumed: only an explicit validated HTTPS result URL may be checked.
  url=row.get("result_url","")
  parsed=urlparse(url)
  if parsed.scheme!="https" or parsed.hostname not in ("sea.bkslab.org","www.sea.bkslab.org"):
   summary.append({"job_id":row.get("job_id"),"state":"NEEDS_VERIFIED_RESULT_URL"});continue
  try:
   res=urllib.request.urlopen(url,timeout=15)
   data=res.read(4_000_000)
   if len(data)<100 or b"Uniprot" not in data and b"Target_Chembl_ID" not in data:
    summary.append({"job_id":row.get("job_id"),"state":"PENDING_OR_UNKNOWN_FORMAT"});continue
   path=Path(run)/"source_archive"/"SEA";path.mkdir(parents=True,exist_ok=True)
   target=path/(str(row["job_id"])+"_"+hashlib.sha256(data).hexdigest()[:12]+".tsv")
   if not target.exists():target.write_bytes(data)
   row.update({"status":"RETRIEVED_UNVERIFIED","raw_file":str(target),"sha256":digest(target)})
   summary.append({"job_id":row.get("job_id"),"state":"RETRIEVED_UNVERIFIED"})
  except Exception as e:summary.append({"job_id":row.get("job_id"),"state":"NETWORK_ERROR","detail":str(e)[:130]})
 save(Path(run)/"job_ledger.json",ledger)
 return summary
def change_detection(run):
 run=Path(run);ledger=read(run/"job_ledger.json");new={}
 for k,v in ledger.items():
  if v.get("sha256"):new[k]=v["sha256"]
 previous=read(run/"input_fingerprints.json")
 changed=[k for k,v in new.items() if previous.get(k)!=v]
 if changed:
  queue=read(run/"work_queue.json")
  for t in queue.get("tasks",[]):
   if t["id"] in ("final_ppi","independent_qc","manuscript_review"):
    t["status"]="QUEUED";t["invalidation_reason"]="새 자료로 입력이 변경됨: "+",".join(changed)
  save(run/"work_queue.json",queue)
  save(run/"change_events.json",{"changed":changed,"changed_at_utc":now(),"next_action":"세부 4 검증 후 세부 3 재실행","primary_network_invalidated":True})
 save(run/"input_fingerprints.json",new)
 return changed
def run_cycle(run):
 run=Path(run);report=review(run)
 queue=read(run/"work_queue.json");status={}
 for t in queue.get("tasks",[]):
  if t["id"] in ("source_reuse_decision","sea_submission","pharmmapper_submission") and report["requires_explicit_approval"] and any(x["decision"]=="PENDING" for x in report["candidates"]):
   t["status"]="WAITING_USER";t["detail"]="기존 분석 자료 검토 후 반영·재분석·보완 선택"
 save(run/"work_queue.json",queue)
 status["pharmmapper"]=poll_pharmmapper(run);status["sea"]=poll_sea(run)
 status["changed_inputs"]=change_detection(run)
 try:
  from np_cytoscape_worker import run as run_cytoscape
  status["cytoscape_preliminary"]=run_cytoscape(run,"preliminary")
  # Final must be marked verified by Agent 4 before execution.
  final=read(run/"final_ppi_manifest.json")
  if final.get("verified_input") and final.get("agent4_preflight_pass") is True:
   status["cytoscape_final"]=run_cytoscape(run,"final")
 except Exception as e:status["cytoscape_error"]=str(e)[:150]
 status["review_candidates"]=len(report["candidates"])
 status["checked_at_utc"]=now()
 save(run/"monitor_latest.json",status)
 return status
def main():
 a=argparse.ArgumentParser();a.add_argument("--workspace",required=True);a.add_argument("--run");a.add_argument("--scan",action="store_true");a.add_argument("--decision",choices=["REUSE_VERIFIED","REANALYZE","SUPPLEMENT","EXCLUDE"]);a.add_argument("--sha");a.add_argument("--proof",default="")
 x=a.parse_args();ws=Path(x.workspace)
 runs=[Path(x.run)] if x.run else list((ws/"runs").glob("*")) if (ws/"runs").exists() else []
 out=[]
 for run in runs:
  if not (run/"request.json").exists():continue
  if x.decision:out.append(decision(run,x.sha,x.decision,x.proof))
  elif x.scan:out.append(review(run))
  else:out.append({"run":str(run),"status":run_cycle(run)})
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
