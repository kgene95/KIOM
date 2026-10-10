from pathlib import Path
import argparse,csv,json,hashlib,urllib.request,urllib.error,datetime,collections
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):
 try:return json.loads(Path(p).read_text(encoding="utf-8"))
 except (FileNotFoundError,ValueError):return {}
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def request(method,url,payload=None):
 data=json.dumps(payload).encode() if payload is not None else None
 req=urllib.request.Request(url,data=data,method=method,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=35) as res:return json.loads(res.read())
def run(run,branch):
 run=Path(run)
 manifest=load(run/(branch+"_ppi_manifest.json"))
 if not manifest.get("verified_input") or manifest.get("branch") not in ("primary","sensitivity","broad_exploratory"):return {"status":"WAITING_VERIFIED_PPI","branch":branch}
 f=Path(manifest.get("network_file",""))
 if not f.is_file() or sha(f)!=manifest.get("input_sha256"):return {"status":"BLOCKED_INPUT_HASH","branch":branch}
 out=run/"cytoscape"/branch;out.mkdir(parents=True,exist_ok=True)
 prior=load(out/"run_manifest.json")
 if prior.get("input_sha256")==sha(f) and prior.get("status")=="COMPLETED":return {"status":"SKIP_UNCHANGED","branch":branch}
 with f.open(encoding="utf-8-sig",newline="") as h:
  items=list(csv.DictReader(h))
 if not items:return {"status":"BLOCKED_EMPTY_PPI","branch":branch}
 edges=[];degree=collections.Counter()
 for row in items:
  a=row.get("preferredName_A") or row.get("source")
  b=row.get("preferredName_B") or row.get("target")
  if not a or not b or a==b:continue
  edges.append({"data":{"source":a,"target":b,"interaction":"STRING"}});degree[a]+=1;degree[b]+=1
 if not edges:return {"status":"BLOCKED_INVALID_EDGES"}
 try:
  request("GET","http://127.0.0.1:1234/v1/version")
 except Exception as e:return {"status":"WAITING_CYTOSCAPE_ONLINE","error":str(e)[:150]}
 nodes=[{"data":{"id":x,"name":x}} for x in sorted(degree)]
 payload={"data":{"name":run.name+"_"+branch+"_"+sha(f)[:8]},"elements":{"nodes":nodes,"edges":edges}}
 try:
  uploaded=request("POST","http://127.0.0.1:1234/v1/networks",payload)
  suid=uploaded.get("networkSUID") or uploaded.get("suid")
  if not suid:return {"status":"FAILED_IMPORT","response":uploaded}
  try:mcode=request("POST","http://127.0.0.1:1234/v1/commands/mcode/cluster",{"network":str(suid)})
  except Exception as e:mcode={"status":"MCODE_FAILED","detail":str(e)}
  save(out/"mcode_response.json",mcode)
  with (out/"degree_rank.csv").open("w",encoding="utf-8-sig",newline="") as h:
   w=csv.writer(h);w.writerow(["gene","degree"])
   for gene,score in sorted(degree.items(),key=lambda x:(-x[1],x[0])):w.writerow([gene,score])
  result={"status":"COMPLETED" if "data" in mcode and not mcode.get("errors") else "PARTIAL_MCODE","run":run.name,"branch":branch,"input_sha256":sha(f),"cytoscape_network_suid":suid,"node_count":len(degree),"edge_count":len(edges),"run_utc":now(),"mcode_result":"PASS" if "data" in mcode else "ERROR","publication_ready":False}
  save(out/"run_manifest.json",result)
  return result
 except Exception as e:return {"status":"FAILED","error":str(e)[:230]}
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--run",required=True);a.add_argument("--branch",choices=["preliminary","final"],default="preliminary");x=a.parse_args()
 print(json.dumps(run(x.run,x.branch),ensure_ascii=False,indent=2))
