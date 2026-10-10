from pathlib import Path
import argparse,csv,hashlib,json,datetime,os,re,sys
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def save(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+".tmp")
 temp.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");os.replace(temp,p)
def load(p,default):return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
def task(key,owner,requires=(),info=None):
 return {"id":key,"agent":owner,"requires":list(requires),"status":"QUEUED","info":info or {},"attempts":0}
def identity_ok(d):
 return bool(d.get("cid") and d.get("smiles") and d.get("structure_qc")=="PASS")
def initialize(root,compound,disease,species):
 if not compound or not disease:raise ValueError("화합물과 질환은 필수입니다.")
 runid=re.sub("[^a-zA-Z0-9_-]","_",compound)[:48]+"_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
 home=root/"runs"/runid;home.mkdir(parents=True,exist_ok=False)
 request={"run_id":runid,"compound_input":compound,"disease_input":disease,"species":species,"created_utc":utc(),"language":"ko","status":"INTAKE","do_docking":False}
 save(home/"request.json",request)
 items=[task("identity","agent1"),task("disease_targets","agent1"),task("structure_handoff","agent1",["identity"]),task("source_reuse_decision","controller",["identity"]),task("sea_submission","agent2",["structure_handoff","source_reuse_decision"]),task("pharmmapper_submission","agent2",["structure_handoff","source_reuse_decision"]),task("sea_collect","agent2",["sea_submission"]),task("pharmmapper_collect","agent2",["pharmmapper_submission"]),task("initial_ppi","agent3",["disease_targets"]),task("final_ppi","agent3",["initial_ppi","sea_collect","pharmmapper_collect"]),task("independent_qc","agent4",["final_ppi"]),task("manuscript_review","agent5",["independent_qc"])]
 save(home/"work_queue.json",{"run_id":runid,"updated_utc":utc(),"tasks":items,"version":1})
 save(home/"execution_state.json",{"state":"INTAKE","created_utc":utc(),"not_complete":True,"next_action":"화합물 CID/구조 검증과 기존 자료 감사"})
 print(json.dumps({"run":str(home),"tasks":len(items)},ensure_ascii=False))
def collect(root):
 qpath=root/"work_queue.json";q=load(qpath,{"tasks":[]})
 identity=load(root/"structure_manifest.json",{})
 request=load(root/"request.json",{})
 handoff=root/"handoff_to_agent2.json"
 if identity_ok(identity):
  structure=identity.get("structure_file")
  verified=not structure or (Path(structure).is_file() and sha(Path(structure))==identity.get("structure_sha256"))
  if verified:
   save(handoff,{"run_id":request.get("run_id"),"cid":identity.get("cid"),"smiles":identity["smiles"],"sdf_or_mol2":structure,"sha256":identity.get("structure_sha256"),"validated_at_utc":utc(),"species":request.get("species"),"submission_approval_required":True})
 for t in q["tasks"]:
  if t["id"]=="identity" and identity_ok(identity):t["status"]="DONE"
  elif t["id"]=="structure_handoff" and handoff.exists():t["status"]="DONE"
  elif t["id"]=="source_reuse_decision":
   choice=load(root/"source_choice.json",{})
   if choice.get("decision") in ("REUSE_VERIFIED","RECOLLECT_NEW") and choice.get("user_approved") is True:t["status"]="DONE"
   elif t["status"]=="QUEUED":t["status"]="WAITING_USER"
  elif t["id"] in ("sea_submission","pharmmapper_submission"):
   doc=load(root/"job_ledger.json",{})
   row=doc.get(t["id"],{})
   if row.get("status") in ("SUBMITTED","PENDING","RETRIEVED","VERIFIED") and row.get("job_id") and row.get("cid")==identity.get("cid") and row.get("input_sha256")==identity.get("structure_sha256"):
    t["status"]="DONE"
   elif all(next(x for x in q["tasks"] if x["id"]==dep)["status"]=="DONE" for dep in t["requires"]):
    t["status"]="NEEDS_EXTERNAL_SUBMISSION"
  elif t["id"] in ("sea_collect","pharmmapper_collect"):
   provider=t["id"].split("_")[0];doc=load(root/"job_ledger.json",{})
   row=doc.get(provider+"_submission",{})
   result=load(root/(provider+"_result_manifest.json"),{})
   if row.get("job_id") and result.get("job_id")==row["job_id"] and result.get("cid")==identity.get("cid") and result.get("verified") is True:
    path=Path(result.get("raw_file",""))
    if path.is_file() and sha(path)==result.get("sha256"):t["status"]="DONE"
   elif row.get("status")=="PENDING":t["status"]="PENDING"
  elif t["id"]=="disease_targets":
   doc=load(root/"disease_target_manifest.json",{})
   if doc.get("verified") is True and doc.get("ontology_id") and doc.get("file") and Path(doc["file"]).is_file():t["status"]="DONE"
  elif t["id"]=="initial_ppi":
   doc=load(root/"preliminary_ppi_manifest.json",{})
   if doc.get("verified_input") is True and doc.get("input_sha256") and doc.get("network_file") and Path(doc["network_file"]).is_file():t["status"]="DONE"
  elif t["id"]=="final_ppi":
   doc=load(root/"final_ppi_manifest.json",{})
   if all(next(x for x in q["tasks"] if x["id"]==dep)["status"]=="DONE" for dep in t["requires"]) and doc.get("verified") is True and doc.get("input_hashes"):t["status"]="DONE"
  elif t["id"]=="independent_qc":
   doc=load(root/"independent_qc.json",{})
   if doc.get("verdict")=="PASS" and next(x for x in q["tasks"] if x["id"]=="final_ppi")["status"]=="DONE":t["status"]="DONE"
  elif t["id"]=="manuscript_review":
   doc=load(root/"manuscript_review.json",{})
   if doc.get("status")=="REVIEWED" and next(x for x in q["tasks"] if x["id"]=="independent_qc")["status"]=="DONE":t["status"]="DONE"
 # Downstream tasks must be invalidated when an upstream gate is no longer satisfied.
 for t in q["tasks"]:
  if t["requires"] and t["status"]=="DONE" and any(next(x for x in q["tasks"] if x["id"]==dep)["status"]!="DONE" for dep in t["requires"]):t["status"]="QUEUED"
 q["updated_utc"]=utc();save(qpath,q)
 print(json.dumps({"run":str(root),"tasks":[{"id":t["id"],"status":t["status"]} for t in q["tasks"]]},ensure_ascii=False))
def main():
 a=argparse.ArgumentParser();a.add_argument("--workspace",required=True);a.add_argument("--new",action="store_true");a.add_argument("--compound",default="");a.add_argument("--disease",default="");a.add_argument("--species",default="Homo sapiens");a.add_argument("--run",default="")
 x=a.parse_args();root=Path(x.workspace)
 if x.new:initialize(root,x.compound,x.disease,x.species)
 else:collect(Path(x.run) if x.run else root)
if __name__=="__main__":main()
