from pathlib import Path
import tempfile,sys,json,hashlib
from unittest.mock import patch
ROOT=Path(r"D:\GPT-CODECX\KIOM\skills\run-network-pharmacology\scripts")
sys.path.insert(0,str(ROOT))
import np_multi_run_monitor as m
def check(cond,msg):
 if not cond:raise AssertionError(msg)
with tempfile.TemporaryDirectory() as td:
 base=Path(td);project=base/"old_project";project.mkdir()
 src=project/"SEA_CID439246.tsv";src.write_text("Target_Chembl_ID\tCID\nCHEMBL2\t439246\n",encoding="utf-8")
 run=base/"NP_Runs"/"runs"/"testcase";run.mkdir(parents=True)
 m.save(run/"request.json",{"run_id":"testcase","compound_input":"CID439246","disease_input":"UC","species":"Homo sapiens"})
 m.save(run/"structure_manifest.json",{"cid":"439246","structure_sha256":"abc"})
 with patch.object(m,"ROOT",base):
  v=m.review(run)
  check(len(v["candidates"])==1,"Existing-source scanner")
  check(v["candidates"][0]["decision"]=="PENDING","Must wait approval")
  source_sha=v["candidates"][0]["sha256"]
  try:m.decision(run,source_sha,"REUSE_VERIFIED","")
  except ValueError:pass
  else:raise AssertionError("Unverified source was reused")
  m.save(run/"verification_evidence.json",{source_sha:{"cid":"439246","species":"Homo sapiens","raw_sha256":source_sha,"job_id":"jobxyz","structure_sha256":"abc","analysis_parameters":{"db":"ChEMBL"},"reviewer_verified":True}})
  v=m.review(run)
  check(v["candidates"][0]["match"]=="COMPOUND_AND_METHOD_VERIFIED","Verified record should unlock reuse")
  m.decision(run,source_sha,"REUSE_VERIFIED","submission_ledger_reviewed")
  v=m.review(run)
  check(v["candidates"][0]["decision"]=="REUSE_VERIFIED","Approval persisted")
  m.save(run/"job_ledger.json",{"sea_submission":{"status":"RETRIEVED_UNVERIFIED","sha256":"newhash"}})
  m.save(run/"work_queue.json",{"tasks":[{"id":x,"status":"DONE"} for x in ["final_ppi","independent_qc","manuscript_review"]]})
  diff=m.change_detection(run)
  check(diff==["sea_submission"],"Detect changed source")
  queue=m.read(run/"work_queue.json")
  check(all(t["status"]=="QUEUED" for t in queue["tasks"]),"Invalidate dependent final results")
print("PASS: source detection, blocked reuse, verified reuse, persistent approval, change invalidation")
