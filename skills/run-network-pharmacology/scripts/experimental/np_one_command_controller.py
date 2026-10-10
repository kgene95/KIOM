from pathlib import Path
import argparse,csv,hashlib,json,datetime,shutil,subprocess,sys,time,traceback
ROOT=Path(r"D:\GPT-CODECX")
PROJECT=ROOT/"KIOM_NP_Projects"/"UC_two_compounds_20261010"
SKILL=ROOT/"KIOM"/"skills"/"run-network-pharmacology"
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic_json(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+".tmp")
 tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
 tmp.replace(path)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit_sea():
 src=ROOT/"KIOM_NP_Projects"/"CMPE_NP"
 dst=PROJECT/"source_archive"/"sea_verified_reuse"
 rows=[];summary=[]
 for folder in sorted(src.glob("sea_result_*")):
  job=folder.name.removeprefix("sea_result_")
  count=0
  for file in sorted(folder.iterdir()):
   if not file.is_file():continue
   dest=dst/folder.name/file.name;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():
    if sha(file)!=sha(dest):raise ValueError("Archive collision: "+str(dest))
   else:shutil.copy2(file,dest)
   if sha(file)!=sha(dest):raise ValueError("Archive checksum mismatch: "+str(file))
   rows.append({"job_id":job,"original":str(file),"archive":str(dest),"sha256":sha(file),"bytes":file.stat().st_size,"compound_assignment":"UNVERIFIED"})
   count+=1
  table={}
  for name in ("sea_result.tsv","sea_result_all.tsv"):
   f=folder/name
   if f.exists():
    with f.open(encoding="utf-8-sig",newline="") as h:reader=csv.DictReader(h,delimiter="\t");table[name]=sum(1 for _ in reader)
  summary.append({"job_id":job,"files":count,"tables":table})
 if not rows:raise RuntimeError("No SEA source files")
 with (PROJECT/"sea_reuse_verification.csv").open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 state_path=PROJECT/"execution_state.json"
 state=json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
 state["sea_reuse_approval"]={"decision":"REUSE_VERIFIED","user_approved":True,"source":str(src),"archive":str(dst),"verified_files":len(rows),"sha256_verified":True,"compound_assignment":"PENDING_VERIFICATION","originals_preserved":True}
 state["state"]="SOURCE_AUDIT";state["next_action"]="Resolve SEA compound/job identity using submission evidence before frozen primary run";state["last_updated_utc"]=stamp()
 atomic_json(state_path,state)
 return {"files":len(rows),"jobs":summary,"originals_preserved":True}
def retry_step(name,fn,attempts=3):
 issues=[]
 for i in range(1,attempts+1):
  try:return {"step":name,"status":"OK","attempt":i,"result":fn()}
  except Exception as e:
   issues.append({"attempt":i,"error":str(e),"at":stamp()})
   if i<attempts:time.sleep(min(2**(i-1),5))
 return {"step":name,"status":"BLOCKED","attempts":issues}
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--mode",choices=["source-audit","status"],default="source-audit")
 args=parser.parse_args()
 PROJECT.mkdir(parents=True,exist_ok=True)
 if args.mode=="source-audit":result=retry_step("SEA source archival audit",audit_sea)
 else:
  p=PROJECT/"execution_state.json"
  result=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"state":"NOT_INITIALIZED"}
 atomic_json(PROJECT/"np_controller_last_run.json",{"created_utc":stamp(),"mode":args.mode,"result":result})
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
 if isinstance(result,dict) and result.get("status")=="BLOCKED":sys.exit(2)
if __name__=="__main__":main()