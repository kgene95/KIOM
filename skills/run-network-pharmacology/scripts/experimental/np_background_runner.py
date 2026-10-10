from pathlib import Path
import argparse,csv,datetime,hashlib,json,os,subprocess,sys,traceback
BASE=Path(r"D:\GPT-CODECX")
PROJECT=BASE/"KIOM_NP_Projects"/"UC_two_compounds_20261010"
SCRIPT=BASE/"np_web_full"/"scripts"/"np_background_runner.py"
CMD=BASE/"np_web_full"/"scripts"/"np_background_runner.cmd"
TASK="KIOM_NP_Watchdog"
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(p.suffix+".new");t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8");os.replace(t,p)
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()
def run_once():
 out=PROJECT/"background_monitor"
 out.mkdir(exist_ok=True)
 lock=out/"running.lock"
 if lock.exists():
  try:
   old=json.loads(lock.read_text(encoding="utf-8"))
   oldtime=datetime.datetime.fromisoformat(old["started"])
   if (datetime.datetime.now(datetime.timezone.utc)-oldtime).total_seconds()<600:
    print("SKIP_RUNNING");return 0
  except Exception:pass
 atomic(lock,{"pid":os.getpid(),"started":now()})
 try:
  state=json.loads((PROJECT/"execution_state.json").read_text(encoding="utf-8"))
  index=PROJECT/"sea_reuse_verification.csv"
  errors=[];n=0
  with index.open(encoding="utf-8-sig",newline="") as f:
   for row in csv.DictReader(f):
    for field in ("original","archive"):
     path=Path(row[field])
     if not path.exists():errors.append("MISSING "+str(path));continue
     if digest(path)!=row["sha256"]:errors.append("HASH_MISMATCH "+str(path))
    n+=1
  approval=state.get("sea_reuse_approval",{}).get("user_approved") is True
  identity=state.get("sea_job_compound_assignment",{})
  jobs=("41debffd05f4","47e4702598a2")
  resolved=all(isinstance(identity.get(j),dict) and identity[j].get("verified") is True and identity[j].get("evidence") for j in jobs)
  if errors:status="SOURCE_INTEGRITY_ERROR";next_action="Repair from untouched originals or request user input"
  elif not approval:status="WAITING_USER_APPROVAL";next_action="Approve reuse or recollection"
  elif not resolved:status="WAITING_SCIENTIFIC_QC";next_action="Verify original SEA job/compound submission metadata; no inference from filename"
  else:status="READY_FOR_NEXT_QC";next_action="Run independent mapping and disease universe QC before full NP pipeline"
  report={"checked_at_utc":now(),"status":status,"rows_verified":n,"files_hashed":n*2,"errors":errors[:20],"next_action":next_action,"remote_model_calls":0,"source_origins_unchanged":not errors,"remaining_gates":state.get("blocking_gates",[])}
  atomic(out/"latest_status.json",report)
  with (out/"monitor_history.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(report,ensure_ascii=False)+"\n")
  print(json.dumps(report,ensure_ascii=False,indent=2))
  return 0 if not errors else 2
 finally:lock.unlink(missing_ok=True)
def install():
 python=BASE/"np_web_full"/".venv"/"Scripts"/"python.exe"
 CMD.write_text("@echo off\r\n\""+str(python)+"\" \""+str(SCRIPT)+"\" --once >> \""+str(PROJECT/"background_monitor"/"task_stdout.log")+"\" 2>&1\r\n",encoding="utf-8")
 cmd=["schtasks.exe","/Create","/F","/SC","MINUTE","/MO","30","/TN",TASK,"/TR",str(CMD)]
 r=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace")
 print("SCHEDULE_CREATE_CODE",r.returncode,r.stdout.strip(),r.stderr.strip())
 q=subprocess.run(["schtasks.exe","/Query","/TN",TASK,"/FO","LIST"],capture_output=True,text=True,encoding="utf-8",errors="replace")
 print("SCHEDULE_QUERY_CODE",q.returncode,q.stdout[:1800],q.stderr[:400])
 return 0 if r.returncode==0 and q.returncode==0 else 3
def main():
 a=argparse.ArgumentParser()
 a.add_argument("--once",action="store_true");a.add_argument("--install",action="store_true")
 x=a.parse_args()
 try:
  (PROJECT/"background_monitor").mkdir(exist_ok=True)
  if x.install:
   result=run_once()
   installed=install()
   return installed if installed else result
  return run_once()
 except Exception:
  print(traceback.format_exc());return 4
if __name__=="__main__":sys.exit(main())