"""Source identity tagging for SEA and PharmMapper; standard library only.

Never edit a raw result. Keep job and compound linkage independently verified.
"""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,os,re
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()
def atomic(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+".tmp")
 tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
 os.replace(tmp,path)
def make_tag(run_id,cid,structure_hash):
 if not re.fullmatch(r"[0-9]+",str(cid)):raise ValueError("CID 숫자 검증 필요")
 if not re.fullmatch(r"[A-Za-z0-9_-]+",str(run_id)):raise ValueError("RUN_ID 형식 확인 필요")
 if not re.fullmatch(r"[a-f0-9]{64}",structure_hash):raise ValueError("구조 SHA-256 검증 필요")
 return "NP-"+str(cid)+"-"+hashlib.sha256((run_id+"|"+str(cid)+"|"+structure_hash).encode()).hexdigest()[:12]
def prepare(run,provider):
 run=Path(run);req=json.loads((run/"request.json").read_text(encoding="utf-8"))
 identity=json.loads((run/"structure_manifest.json").read_text(encoding="utf-8"))
 cid=str(identity.get("cid",""));structure=Path(identity.get("structure_file",""))
 sh=identity.get("structure_sha256","")
 if identity.get("structure_qc")!="PASS" or not identity.get("smiles"):raise ValueError("화합물 SMILES/정체성 검증이 필요합니다")
 if not structure.is_file() or sha(structure)!=sh:raise ValueError("구조 파일과 SHA가 불일치합니다")
 if provider not in ("SEA","PharmMapper"):raise ValueError("지원하지 않는 소스")
 if provider=="PharmMapper" and structure.suffix.lower() not in (".sdf",".mol2"):raise ValueError("PharmMapper 구조 형식 오류")
 tag=make_tag(req["run_id"],cid,sh)
 item={"compound_tag":tag,"run_id":req["run_id"],"compound_name":identity.get("compound_name",req.get("compound_input")),"cid":cid,"smiles":identity["smiles"],"structure_sha256":sh,"structure_file":str(structure),"species":req.get("species"),"provider":provider,"prepared_at_utc":utc(),"submission_status":"PREPARED_NOT_SUBMITTED","job_id":None}
 manifest=run/"submissions"/(provider+"_"+tag+".json")
 if manifest.exists():
  old=json.loads(manifest.read_text(encoding="utf-8"))
  for key in ("compound_tag","cid","structure_sha256","provider"):
   if old.get(key)!=item.get(key):raise ValueError("기존 제출 태그 충돌")
  return old
 atomic(manifest,item)
 return item
def record_result(run,provider,tag,job_id,raw_path,submission_evidence):
 run=Path(run);path=run/"submissions"/(provider+"_"+tag+".json")
 if not path.exists():raise ValueError("제출 전 생성한 태그가 없습니다")
 job=json.loads(path.read_text(encoding="utf-8"))
 if job.get("compound_tag")!=tag or job.get("provider")!=provider:raise ValueError("태그 불일치")
 if not job_id or not submission_evidence:raise ValueError("공식 작업 ID와 제출 증거 필요")
 if job.get("job_id") and job["job_id"]!=str(job_id):raise ValueError("작업 ID가 다릅니다")
 if job.get("submission_status") not in ("SUBMITTED","PENDING","PREPARED_NOT_SUBMITTED"):raise ValueError("제출 상태 검토 필요")
 # Prepared state cannot be promoted merely by possessing downloaded results.
 if job["submission_status"]=="PREPARED_NOT_SUBMITTED":raise ValueError("실제 제출 기록 검증 전에는 결과 확정 불가")
 raw=Path(raw_path)
 if not raw.is_file():raise ValueError("원본 결과 없음")
 sidecar={"compound_tag":tag,"cid":job["cid"],"provider":provider,"job_id":str(job_id),"submission_evidence":submission_evidence,"structure_sha256":job["structure_sha256"],"raw_file":str(raw),"raw_sha256":sha(raw),"source_status":"RETRIEVED_IDENTITY_QC_PENDING","saved_at_utc":utc()}
 target=run/"source_archive_index"/(provider+"_"+tag+"_"+str(job_id)+".json")
 if target.exists():
  old=json.loads(target.read_text(encoding="utf-8"))
  if old["raw_sha256"]!=sidecar["raw_sha256"]:raise ValueError("기존 원본 충돌: 덮어쓰기 금지")
  return old
 atomic(target,sidecar)
 return sidecar
if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--run",required=True);parser.add_argument("--provider",required=True,choices=["SEA","PharmMapper"])
 opts=parser.parse_args()
 print(json.dumps(prepare(opts.run,opts.provider),ensure_ascii=False,indent=2))
