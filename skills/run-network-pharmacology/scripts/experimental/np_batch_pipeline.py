from pathlib import Path
import argparse,json,datetime,csv,hashlib,subprocess,sys,time
BASE=Path(r"D:\GPT-CODECX\np_web_full")
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(path,obj):
 temp=path.with_suffix(path.suffix+".tmp")
 temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
 temp.replace(path)
def runner(project,mode):
 statefile=project/"execution_state.json"
 state=json.loads(statefile.read_text(encoding="utf-8")) if statefile.exists() else {}
 events=state.setdefault("batch_events",[])
 def event(stage,status,detail):
  events.append({"utc":now(),"stage":stage,"status":status,"detail":detail})
  state["last_updated_utc"]=now();write(statefile,state)
 def hold(reason):
  state["state"]="WAITING_QC";state["overall_status"]="IN_PROGRESS";state["next_action"]=reason
  event("gate","WAITING",reason)
  return 3
 if mode=="status":
  print(json.dumps(state,ensure_ascii=False,indent=2))
  return 0
 approvals=state.get("sea_reuse_approval",{})
 if not approvals.get("user_approved"):return hold("Existing SEA data requires explicit user reuse/recollection approval")
 raw=project/"source_archive"/"sea_verified_reuse"
 for job in ("41debffd05f4","47e4702598a2"):
  for filename in ("sea_result_all.tsv","sea_result.tsv"):
   f=raw/("sea_result_"+job)/filename
   if not f.is_file():return hold("SEA raw file missing: "+str(f))
 event("raw_sea","PASS","Both SEA jobs archived; no raw data overwritten")
 if mode=="source-check":
  print("SOURCE_CHECK_PASS",str(raw))
  return 0
 assignment=state.get("sea_job_compound_assignment",{})
 required={"41debffd05f4","47e4702598a2"}
 if not required.issubset(assignment.keys()):return hold("Verify job IDs against original SEA submission metadata, then set sea_job_compound_assignment with evidence")
 mapped={str(assignment[j].get("cid")) for j in required if isinstance(assignment[j],dict) and assignment[j].get("verified") is True and assignment[j].get("evidence")}
 if mapped!={"439246","56776173"}:return hold("SEA assignment lacks verified evidence for both exact compound CIDs")
 if not state.get("human_mapping_qc_passed"):return hold("Independent human HGNC/UniProt mapping QC must pass")
 if not state.get("uc_disease_universe_frozen"):return hold("UC disease gene universe must be frozen with provenance")
 if not state.get("primary_branch_frozen"):return hold("Final primary compound target branch must be frozen")
 event("gates","PASS","All primary scientific gates explicitly verified")
 # Deliberately only run pre-registered reviewed deterministic stages, not arbitrary shell strings.
 stage_script=BASE/"scripts"/"rerun_project_with_sea.py"
 manifest=project/"00_project"/"NP_manifest.json"
 if not manifest.is_file():return hold("Primary project layout/manifest missing; migration and validation required")
 for attempt in range(1,4):
  proc=subprocess.run([sys.executable,str(stage_script),str(project)],capture_output=True,text=True,timeout=1200)
  log=project/("np_batch_attempt_"+str(attempt)+".log")
  log.write_text(proc.stdout+"\n"+proc.stderr,encoding="utf-8")
  if proc.returncode==0:
   event("NP_CORE","PASS",str(log))
   state["state"]="INDEPENDENT_QC";state["overall_status"]="IN_PROGRESS"
   write(statefile,state)
   print("CORE_EXECUTED_QC_PENDING")
   return 0
  event("NP_CORE","FAILED_ATTEMPT_"+str(attempt),str(log))
  if attempt<3:time.sleep(min(2**attempt,10))
 return hold("NP core failed three times; inspect local logs and select a documented alternative method")
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--project",required=True)
 ap.add_argument("--mode",choices=["status","source-check","pipeline"],default="pipeline")
 args=ap.parse_args()
 p=Path(args.project)
 if not p.exists():raise SystemExit("PROJECT_NOT_FOUND")
 code=runner(p,args.mode)
 print("EXIT_STATUS",code)
 sys.exit(code)
if __name__=="__main__":main()
