from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs,urlparse
import json,secrets,html,os
import np_multi_run_monitor as m
WORKSPACE=Path(os.getenv("NP_RUN_WORKSPACE",r"D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs"))
TOKEN=secrets.token_urlsafe(24)
def h(s):return html.escape(str(s),quote=True)
def layout(content):
 return """<!doctype html><html lang="ko"><meta charset="utf-8"><title>NP 연구 관리자</title><style>body{font:16px Arial,sans-serif;margin:40px auto;max-width:1080px;color:#26323c}section{border:1px solid #ddd;padding:18px;border-radius:12px;margin:14px 0}button{padding:10px;margin:4px;cursor:pointer}label{display:block;margin:10px 0}input,select{padding:9px}.muted{color:#777}.warn{color:#9e6113}</style><h2>NP 총괄 에이전트 · 기존 자료 우선 확인</h2>"""+content+"</html>"
def form(action,fields,button):
 # Explicit browser confirmation; no implicit submission or raw-data overwrites.
 confirm=(' onsubmit="return confirm(\'선택한 분석 방식을 승인하고 기록하시겠습니까? 기존 원본은 보존됩니다.\')"' if action=="/decide" else "")
 return '<form method="post" action="'+h(action)+'"'+confirm+'><input type="hidden" name="token" value="'+h(TOKEN)+'">'+fields+'<button type="submit">'+h(button)+'</button></form>'
def app_index():
 bits=['<p class="muted">로컬 전용 화면 · 검증 안 된 자료는 자동 사용하거나 재제출하지 않습니다.</p>']
 fields='<p class="muted">화합물을 한 줄에 하나씩 입력하세요. 추가 버튼으로 늘릴 수 있습니다. 쉼표 입력도 분리되지만 버튼을 권장합니다.</p>'
 fields+='<div id="compounds"><label>화합물 1 <input name="compound" required placeholder="Naringenin 또는 CID 439246"></label></div>'
 fields+='<button type="button" onclick="addCompound()">+ 화합물 추가</button>'
 fields+='<label>질환명 <input name="disease" required placeholder="Ulcerative colitis"></label>'
 fields+='<label>생물종 <select name="species"><option>Homo sapiens</option><option>Mus musculus</option><option>Rattus norvegicus</option></select></label>'
 fields+='<script>function addCompound(){const root=document.getElementById("compounds");const n=root.querySelectorAll("input").length+1;const label=document.createElement("label");label.textContent="화합물 "+n+" ";const inp=document.createElement("input");inp.name="compound";inp.required=true;inp.placeholder="화합물명 또는 CID";const del=document.createElement("button");del.type="button";del.textContent="삭제";del.onclick=()=>label.remove();label.append(inp,del);root.append(label)}</script>'
 bits.append('<section><h3>새 소재 등록</h3>'+form('/new',fields,'등록하고 기존 자료 탐색')+'</section>')
 for run in sorted((WORKSPACE/"runs").glob("*")) if (WORKSPACE/"runs").exists() else []:
  req=m.read(run/"request.json")
  if not req:continue
  review=m.read(run/"existing_data_review.json")
  bits.append('<section><h3>'+h(req.get("compound_input"))+' / '+h(req.get("disease_input"))+'</h3><div class="muted">'+h(run.name)+'</div>')
  bits.append('<p>기존 자료 후보 '+str(len(review.get("candidates",[])))+'건 · 파일명 일치만으로는 검증 완료가 아닙니다.</p>')
  bits.append(form("/scan",'<input type="hidden" name="run" value="'+h(run.name)+'">','기존 자료 다시 검색'))
  approval=m.read(run/"initial_approval.json")
  status="승인됨" if approval.get("user_approved") is True else "승인 필요"
  bits.append('<div><h4>최초 통합 승인 · '+h(status)+'</h4><p class="muted">기존 자료 검증 후 필요한 작업만 실행합니다. 이메일 주소·암호·인증코드는 저장하지 않습니다.</p>')
  fields='<input type="hidden" name="run" value="'+h(run.name)+'">'
  fields+='<label>기존 자료 처리 <select name="reuse"><option value="REUSE_ONLY_VERIFIED">검증된 기존 자료만 반영</option><option value="REVIEW_EACH">자료별로 승인</option></select></label>'
  fields+='<label><input type="checkbox" name="supplement" value="yes"> 검증 후 부족한 부분의 보완 분석 허용 (범위 변경 시 재확인)</label>'
  fields+='<label><input type="checkbox" name="new_submit" value="yes"> 기존 검증 자료가 없을 때 SEA·PharmMapper 신규 제출 허용</label>'
  fields+='<label><input type="checkbox" name="email_notify" value="yes"> PharmMapper 결과 알림 이메일 사용 (실제 주소는 별도 비공개 입력)</label>'
  fields+='<label><input type="checkbox" name="remote_work" value="yes"> 승인된 원격 PC에서 작업 실행 요청 허용 (운영체제 승인 별개)</label>'
  bits.append(form("/approve",fields,"최초 분석 범위 승인")+"</div>")
  for v in review.get("candidates",[]):
   bits.append('<div style="border-top:1px solid #ddd;margin-top:10px;padding-top:10px"><strong>'+h(v["source"])+'</strong> '+h(v["match"])+' / '+h(v["decision"])+'<p class="muted">'+h(v["source_file"])+'</p>')
   bits.append('<p>검증 근거: '+h(v.get("proof"))+'</p>')
   for act,label in (("REUSE_VERIFIED","검증된 자료 반영 및 재분석"),("SUPPLEMENT","부족한 부분 보완"),("REANALYZE","새로 분석"),("EXCLUDE","해당 자료 제외")):
    data='<input type="hidden" name="run" value="'+h(run.name)+'"><input type="hidden" name="sha" value="'+h(v["sha256"])+'"><input type="hidden" name="decision" value="'+act+'">'
    data+='<label>승인 사유/제출 근거 <input name="proof" placeholder="검증 자료 또는 사유"></label>'
    bits.append(form("/decide",data,label))
   bits.append('</div>')
  bits.append('</section>')
 return layout(''.join(bits))
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  content=app_index().encode()
  self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(content)));self.end_headers();self.wfile.write(content)
 def do_POST(self):
  n=int(self.headers.get("Content-Length","0"))
  if n>10000:self.send_error(413);return
  parsed=parse_qs(self.rfile.read(n).decode())
  data={k:v[0] for k,v in parsed.items()}
  if data.get("token")!=TOKEN:self.send_error(403);return
  target=urlparse(self.path).path;msg="처리 완료"
  try:
   if target=="/new":
    import np_agent_queue as q
    import re
    raw=parsed.get("compound",[])
    names=[part.strip() for entry in raw for part in re.split(r"[,;\n]+",entry) if part.strip()]
    names=list(dict.fromkeys(names))
    if not names or len(names)>20:raise ValueError("화합물은 1~20개 입력하세요")
    existing=[m.read(a/"request.json") for a in (WORKSPACE/"runs").glob("*")] if (WORKSPACE/"runs").exists() else []
    created=[]
    for name in names:
     duplicate=next((x for x in existing if x.get("compound_input","").casefold()==name.casefold() and x.get("disease_input","").casefold()==data.get("disease","").casefold() and x.get("species")==data.get("species","Homo sapiens")),None)
     if duplicate:continue
     home=q.initialize(WORKSPACE,name,data.get("disease",""),data.get("species","Homo sapiens"))
     m.review(home)
     created.append(name)
    msg="새 분석 생성: "+", ".join(created) if created else "동일한 화합물·질환·생물종 작업이 이미 등록돼 있습니다. 중복 생성하지 않았습니다."
   else:
    id=data.get("run","")
    if not id or Path(id).name!=id:raise ValueError("유효하지 않은 작업")
    run=WORKSPACE/"runs"/id
    if not (run/"request.json").exists():raise ValueError("작업을 찾을 수 없음")
    if target=="/scan":m.review(run)
    elif target=="/approve":
     status=m.read(run/"existing_data_review.json")
     # This high-level approval never lifts per-file scientific verification or OS security prompts.
     approval={"user_approved":True,"approved_at_utc":m.now(),"reuse_policy":data.get("reuse","REVIEW_EACH"),"supplement_authorized":data.get("supplement")=="yes","new_submission_authorized":data.get("new_submit")=="yes","email_notification_authorized":data.get("email_notify")=="yes","remote_work_requested":data.get("remote_work")=="yes","reviewed_candidates":len(status.get("candidates",[])),"limitations":"Scientific QC, individual unverified source reuse, OS approval, CAPTCHA, logins and provider terms remain mandatory."}
     m.save(run/"initial_approval.json",approval)
    elif target=="/decide":m.decision(run,data.get("sha",""),data.get("decision",""),data.get("proof",""))
    else:raise ValueError("알 수 없는 동작")
  except Exception as e:msg="처리하지 못했습니다: "+str(e)
  output=layout('<p>'+h(msg)+'</p><p><a href="/">돌아가기</a></p>').encode()
  self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers();self.wfile.write(output)
if __name__=="__main__":
 WORKSPACE.mkdir(parents=True,exist_ok=True)
 print("LOCAL_DASHBOARD http://127.0.0.1:8765",flush=True)
 ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
