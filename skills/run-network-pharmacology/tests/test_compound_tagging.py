from pathlib import Path
import tempfile,sys,json,hashlib
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import np_compound_tagging as t
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/"request.json").write_text(json.dumps({"run_id":"RUN_TEST","compound_input":"Naringenin","species":"Homo sapiens"}),encoding="utf-8")
 sdf=p/"naringenin.sdf";sdf.write_text("TEST VALIDATED STRUCTURE FIXTURE",encoding="utf-8")
 h=t.sha(sdf)
 (p/"structure_manifest.json").write_text(json.dumps({"cid":"439246","compound_name":"Naringenin","smiles":"C1=CC=CC=C1","structure_qc":"PASS","structure_file":str(sdf),"structure_sha256":h}),encoding="utf-8")
 a=t.prepare(p,"SEA");b=t.prepare(p,"SEA");assert a["compound_tag"]==b["compound_tag"]
 assert "439246" in a["compound_tag"]
 c=t.prepare(p,"PharmMapper");assert c["compound_tag"]==a["compound_tag"]
 source=p/"sea.tsv";source.write_text("row\n",encoding="utf-8")
 try:t.record_result(p,"SEA",a["compound_tag"],"ABC",""+str(source),"submission_id_proof")
 except ValueError:pass
 else:raise AssertionError("Unsubmitted result accepted")
 side=p/"submissions"/("SEA_"+a["compound_tag"]+".json")
 record=json.loads(side.read_text(encoding="utf-8"));record["submission_status"]="SUBMITTED";record["job_id"]="ABC";t.atomic(side,record)
 res=t.record_result(p,"SEA",a["compound_tag"],"ABC",source,"submission_id_proof")
 assert res["raw_sha256"]==t.sha(source)
 assert source.read_text()=="row\n"
 assert t.record_result(p,"SEA",a["compound_tag"],"ABC",source,"submission_id_proof")["raw_sha256"]==res["raw_sha256"]
 source.write_text("new content\n",encoding="utf-8")
 try:t.record_result(p,"SEA",a["compound_tag"],"ABC",source,"submission_id_proof")
 except ValueError:pass
 else:raise AssertionError("Raw collision was overwritten")
 print("PASS: per-compound tag, deterministic same-run identity, submission gate, raw checksums, no overwrite",flush=True)
