from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote
import json, secrets, html, os, re, requests, hashlib, datetime
import np_multi_run_monitor as m

WORKSPACE = Path(os.getenv("NP_RUN_WORKSPACE", r"D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs"))
TOKEN = secrets.token_urlsafe(24)
SESSION_PHARMMAPPER_EMAIL = {}

def h(value):
    return html.escape(str(value), quote=True)

def project_root(root=WORKSPACE):
    return Path(root)/"projects"

def project_path(project_id, root=WORKSPACE):
    if Path(project_id).name != project_id:
        raise ValueError("유효하지 않은 프로젝트")
    return project_root(root)/project_id/"project.json"

def read_project(project_id, root=WORKSPACE):
    return m.read(project_path(project_id, root))

def save_project(project, root=WORKSPACE):
    path=project_path(project["project_id"], root)
    path.parent.mkdir(parents=True, exist_ok=True)
    m.save(path, project)

def create_project(name, root=WORKSPACE):
    label=name.strip() or "새 네트워크 약리 프로젝트"
    slug=re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", label).strip("_")[:48] or "project"
    project_id=slug+"_"+m.now().replace(":", "").replace("-", "").replace("T", "_").replace("Z", "")+"_"+secrets.token_hex(3)
    project={"project_id":project_id,"name":label,"created_at_utc":m.now(),"updated_at_utc":m.now(),"status":"DRAFT","run_ids":[]}
    save_project(project, root)
    return project

def list_projects(root=WORKSPACE):
    directory=project_root(root)
    if not directory.exists(): return []
    projects=[m.read(path) for path in directory.glob("*/project.json")]
    return sorted((p for p in projects if p), key=lambda p:p.get("updated_at_utc",""), reverse=True)

def layout(content):
    return """<!doctype html><html lang="ko"><meta charset="utf-8"><title>NP 연구 관리자</title>
<style>body{font:16px Arial,sans-serif;margin:40px auto;max-width:1080px;color:#26323c}section{border:1px solid #ddd;padding:18px;border-radius:12px;margin:14px 0}button{padding:10px;margin:4px;cursor:pointer}label{display:block;margin:10px 0}input,select,textarea{padding:9px;min-width:280px}textarea{min-height:110px;width:500px;max-width:100%;font:inherit}.muted{color:#667}.warn{color:#9e6113}.ok{color:#177245}table{border-collapse:collapse;width:100%;margin:10px 0}th,td{border:1px solid #ddd;padding:8px;text-align:left}</style>
<h2>NP 총괄 에이전트 · 기존 자료 우선 확인</h2>""" + content + "<script>if(location.hash){const item=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(item){item.open=true;item.scrollIntoView({block:'start'});}}</script></html>"

def form(action, fields, button):
    return '<form method="post" action="'+h(action)+'"><input type="hidden" name="token" value="'+h(TOKEN)+'">'+fields+'<button type="submit">'+h(button)+'</button></form>'

def compound_queries(value):
    """Return unique compound names/CIDs supplied one per line, preserving order."""
    queries = []
    seen = set()
    for raw in value.splitlines():
        query = raw.strip()
        key = query.casefold()
        if query and key not in seen:
            queries.append(query)
            seen.add(key)
    return queries

def cid_candidates(query):
    query = query.strip()
    if not query:
        return []
    cid_match = re.fullmatch(r"(?:CID\s*[:#]?\s*)?(\d+)", query, flags=re.I)
    try:
        if cid_match:
            cids = [cid_match.group(1)]
        else:
            response = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"+quote(query, safe="")+"/cids/JSON", timeout=15)
            response.raise_for_status()
            cids = [str(x) for x in response.json().get("IdentifierList", {}).get("CID", [])[:10]]
        if not cids:
            return []
        response = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"+",".join(cids)+"/property/Title,IUPACName,MolecularFormula,InChIKey,CanonicalSMILES/JSON", timeout=15)
        response.raise_for_status()
        rows = response.json().get("PropertyTable", {}).get("Properties", [])
        return [{"cid":str(x["CID"]), "title":x.get("Title") or x.get("IUPACName") or "Unnamed compound", "iupac":x.get("IUPACName",""), "formula":x.get("MolecularFormula",""), "inchikey":x.get("InChIKey",""), "smiles":x.get("ConnectivitySMILES") or x.get("CanonicalSMILES","")} for x in rows]
    except Exception:
        return []

def approval_fields(run_id, review, include_email=True):
    candidate_count=len(review.get("candidates", []))
    fields='<input type="hidden" name="run" value="'+h(run_id)+'">'
    if candidate_count == 0:
        fields+='<p class="ok">기존 자료가 없으므로 신규 제출 경로만 선택합니다.</p>'
        fields+='<label><input type="checkbox" name="new_submit" value="yes"> SEA·PharmMapper 신규 제출 허용</label>'
    else:
        fields+='<p class="ok">기존 자료를 사용할지 먼저 결정하고, 부족한 경우에만 보완 신규 제출을 허용할 수 있습니다.</p>'
        fields+='<label>기존 자료 처리 <select name="reuse"><option value="REUSE_ONLY_VERIFIED">검증된 기존 자료 사용</option><option value="REVIEW_EACH">자료별 검증 후 결정</option><option value="DO_NOT_REUSE">기존 자료 사용하지 않음</option></select></label>'
        fields+='<label><input type="checkbox" name="supplement" value="yes"> 기존 자료 검증 후 부족한 부분에 한해 SEA·PharmMapper 보완 신규 제출 허용</label>'
    fields+='<label><input type="checkbox" name="email_notify" value="yes"> PharmMapper 완료 알림 이메일 사용</label>'
    if include_email:
        fields+='<label>PharmMapper 제출·결과 수신 이메일 (현재 세션 전용) <input type="email" name="pharmmapper_email" autocomplete="email" placeholder="name@example.org"></label><p class="muted">주소는 한 번만 입력하며 현재 브라우저·서버 메모리에만 유지됩니다. 프로젝트 기록, 로그, 원본 파일, 보고서에는 저장하지 않습니다.</p>'
    else:
        fields+='<p class="muted">PharmMapper 이메일은 이 화면의 첫 화합물에 한 번만 입력합니다.</p>'
    return fields

def decision_status(approval):
    return "분석 경로 확정 완료" if approval.get("user_approved") is True else "결정 필요"

def run_panel(run, include_email=True):
    req=m.read(run/"request.json")
    review=m.read(run/"existing_data_review.json")
    candidate_count=len(review.get("candidates", []))
    approval=m.read(run/"initial_approval.json")
    email_status="입력됨 (현재 세션만)" if "__shared__" in SESSION_PHARMMAPPER_EMAIL else "미입력"
    bits=['<section><h3>'+h(req.get("compound_input"))+' / '+h(req.get("disease_input"))+'</h3><div class="muted">'+h(run.name)+'</div>']
    bits.append('<p>확인 CID: <strong>'+h(req.get("compound_cid","기록 없음"))+'</strong> · 기존 자료 후보 '+str(candidate_count)+'건</p>')
    if approval.get("user_approved") is True:
        bits.append('<p class="ok"><strong>분석 경로 확정 완료</strong> · '+h(approval.get("approved_at_utc","저장 시각 없음"))+'</p>')
        bits.append('<p class="muted">저장 경로: '+h(approval.get("analysis_path","기록 없음"))+'</p>')
        bits.append(form("/reopen_decision", '<input type="hidden" name="run" value="'+h(run.name)+'">', "재결정")+'</section>')
        return ''.join(bits)
    bits.append(form("/scan", '<input type="hidden" name="run" value="'+h(run.name)+'">', "기존 자료 다시 탐색"))
    bits.append('<div><h4>3. 분석 경로 결정</h4><p class="muted">PharmMapper 이메일: '+email_status+'</p>')
    for v in review.get("candidates",[]):
        bits.append('<div style="border-top:1px solid #ddd;margin-top:10px;padding-top:10px"><strong>'+h(v["source"])+'</strong> '+h(v["match"])+' / '+h(v["decision"])+'<p class="muted">'+h(v["source_file"])+'</p><p>검증 근거: '+h(v.get("proof"))+'</p></div>')
    bits.append('<p><a href="https://www.lilab-ecust.cn/pharmmapper/" target="_blank" rel="noopener">PharmMapper 공식 제출 화면 열기</a></p>')
    bits.append(form("/approve", approval_fields(run.name, review, include_email=include_email), "이 화합물의 분석 경로 확정")+'</div></section>')
    return ''.join(bits)

def decision_page(run_ids, notice=""):
    panels=[]
    for index, run_id in enumerate(run_ids):
        if Path(run_id).name != run_id: continue
        run=WORKSPACE/"runs"/run_id
        if (run/"request.json").exists():
            panels.append(run_panel(run, include_email=(index == 0 and "__shared__" not in SESSION_PHARMMAPPER_EMAIL)))
    message='<section><p class="ok">'+h(notice)+'</p></section>' if notice else ''
    return layout(message+'<h3>다음 단계: 화합물별 분석 경로 결정</h3>'+''.join(panels)+'<p><a href="/">새 화합물·질환 등록 화면</a></p>')

def saved_page(project_id, current_run_id, next_run_id=None):
    content='<section><h3>분석 경로가 저장되었습니다.</h3><p class="ok">현재 화합물의 선택 내용이 프로젝트에 중간 저장되었습니다.</p>'
    if next_run_id:
        url='/decision?project='+quote(project_id, safe="")+'&run='+quote(next_run_id, safe="")
        content+='<p><a href="'+h(url)+'"><button>다음 화합물 결정</button></a></p>'
    else:
        url='/project?project='+quote(project_id, safe="")
        content+='<p>이 프로젝트의 모든 화합물 결정이 저장되었습니다.</p><p><a href="'+h(url)+'"><button>프로젝트로 돌아가기</button></a></p>'
    return layout(content+'</section>')

def ensure_project_for_run(run):
    request=m.read(run/"request.json")
    project_id=request.get("project_id", "")
    project=read_project(project_id) if project_id else None
    if project: return project
    siblings=[]
    for candidate in (WORKSPACE/"runs").glob("*") if (WORKSPACE/"runs").exists() else []:
        req=m.read(candidate/"request.json")
        if req and not req.get("project_id") and req.get("disease_input")==request.get("disease_input") and req.get("species")==request.get("species"):
            siblings.append((candidate, req))
    project=create_project('복구: '+str(request.get("disease_input", "기존 분석"))+' 분석')
    project["status"]="LEGACY_RECOVERED"
    project["run_ids"]=[]
    for sibling, req in siblings:
        req["project_id"]=project["project_id"]
        m.save(sibling/"request.json", req)
        project["run_ids"].append(sibling.name)
    project["updated_at_utc"]=m.now()
    save_project(project)
    return project

def next_unapproved_run(project, current_run_id):
    for run_id in project.get("run_ids", []):
        if run_id == current_run_id: continue
        approval=m.read(WORKSPACE/"runs"/run_id/"initial_approval.json")
        if approval.get("user_approved") is not True: return run_id
    return None

def new_compound_form(project_id):
    fields='<input type="hidden" name="project" value="'+h(project_id)+'">'
    fields+='<label>화합물명 또는 CID (한 줄에 하나씩) <textarea name="compound" required placeholder="Naringenin&#10;Vitexin 4-O-glucoside&#10;또는 CID 439246"></textarea></label>'
    fields+='<label>질환명 <input name="disease" required placeholder="Ulcerative colitis"></label>'
    fields+='<label>생물종 <select name="species"><option>Homo sapiens</option><option>Mus musculus</option><option>Rattus norvegicus</option></select></label>'
    return '<details><summary>새 화합물 추가</summary><p class="muted">기존 중간 저장 내용은 유지한 채 이 프로젝트에 화합물을 추가합니다.</p>'+form("/resolve", fields, "PubChem CID 후보 확인")+'</details>'

def zero_candidate_form(project_id, run_ids):
    fields='<input type="hidden" name="project" value="'+h(project_id)+'"><input type="hidden" name="run_ids" value="'+h(','.join(run_ids))+'">'
    fields+='<p class="ok">기존 자료가 없는 화합물은 이 한 번의 승인으로 신규 제출 경로를 설정합니다.</p>'
    fields+='<label><input type="checkbox" name="new_submit" value="yes"> SEA·PharmMapper 신규 제출 허용</label>'
    fields+='<label><input type="checkbox" name="email_notify" value="yes"> PharmMapper 완료 알림 이메일 사용</label>'
    fields+='<label>PharmMapper 제출·결과 수신 이메일 (현재 세션 전용) <input type="email" name="pharmmapper_email" autocomplete="email" placeholder="name@example.org"></label>'
    return '<section><h3>기존 자료 0건 · 신규 제출 간편 승인</h3>'+form("/approve_zero", fields, "신규 제출 경로 확정")+'</section>'

def sha256_file(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()

def begin_run_analysis(run):
    """Prepare immutable PubChem structure evidence and source job tags; never submit externally."""
    import np_agent_queue as q
    import np_compound_tagging as tagging
    run=Path(run)
    request=m.read(run/"request.json")
    approval=m.read(run/"initial_approval.json")
    if approval.get("user_approved") is not True:
        raise ValueError("분석 경로 확정이 필요합니다.")
    cid=str(request.get("compound_cid", ""))
    smiles=str(request.get("compound_smiles", ""))
    if not re.fullmatch(r"\d+", cid) or not smiles:
        raise ValueError("확인된 CID와 SMILES가 있어야 분석을 시작할 수 있습니다.")
    archive=run/"source_archive"/"PubChem"
    archive.mkdir(parents=True, exist_ok=True)
    existing=sorted(archive.glob(cid+"_*.sdf"))
    structure_file=None
    for candidate in existing:
        if candidate.stat().st_size >= 100 and sha256_file(candidate):
            structure_file=candidate
            break
    structure_dimension="archived"
    if structure_file is None:
        attempts=[]
        raw=None
        for record_type in ("3d","2d"):
            url="https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"+cid+"/record/SDF/?record_type="+record_type
            try:
                response=requests.get(url, timeout=20)
                response.raise_for_status()
                candidate=response.content
                if len(candidate) < 100 or b"$$$$" not in candidate:
                    raise ValueError("SDF 원본 형식 확인 실패")
                raw=candidate
                structure_dimension=record_type
                attempts.append({"source":"PubChem PUG REST","record_type":record_type,"url":url,"status":"RETRIEVED","checked_at_utc":m.now()})
                break
            except Exception as error:
                attempts.append({"source":"PubChem PUG REST","record_type":record_type,"url":url,"status":"FAILED","detail":str(error)[:220],"checked_at_utc":m.now()})
        m.save(run/"source_attempts.json",{"compound_cid":cid,"attempts":attempts,"updated_at_utc":m.now()})
        if raw is None:
            raise ValueError("PubChem 3D·2D SDF 원본을 모두 확보하지 못했습니다.")
        raw_hash=hashlib.sha256(raw).hexdigest()
        structure_file=archive/(cid+"_"+raw_hash[:16]+".sdf")
        if not structure_file.exists():
            structure_file.write_bytes(raw)
    structure_hash=sha256_file(structure_file)
    structure={"cid":cid,"smiles":smiles,"compound_name":request.get("compound_title") or request.get("compound_input"),"structure_file":str(structure_file),"structure_sha256":structure_hash,"structure_qc":"PASS","source":"PubChem PUG REST SDF","record_type":structure_dimension,"downloaded_at_utc":m.now()}
    m.save(run/"structure_manifest.json", structure)
    choice={"decision":"RECOLLECT_NEW" if approval.get("new_submission_authorized") else "REUSE_VERIFIED","user_approved":True,"recorded_at_utc":m.now(),"source":"initial_approval","note":"사용자 승인 경로에서 생성; 외부 제출은 아직 수행하지 않음"}
    m.save(run/"source_choice.json", choice)
    q.collect(run)
    prepared=[]
    if approval.get("new_submission_authorized"):
        for provider in ("SEA","PharmMapper"):
            prepared.append(tagging.prepare(run,provider)["provider"])
    queue=m.read(run/"work_queue.json").get("tasks",[])
    task_status={item.get("id"):item.get("status") for item in queue}
    result={"updated_at_utc":m.now(),"status":"LOCAL_PREPARATION_COMPLETE","structure_file":str(structure_file),"structure_sha256":structure_hash,"prepared_providers":prepared,"task_status":task_status,"next_action":"공식 SEA·PharmMapper 제출 필요" if prepared else "기존 자료 검증 또는 보완 경로 확인 필요","external_submission_performed":False}
    m.save(run/"analysis_progress.json",result)
    return result

def submit_pharmmapper(run, email):
    """Submit a prepared V2000 SDF to the official PharmMapper form without persisting email."""
    run=Path(run)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""):
        raise ValueError("PharmMapper 제출에는 유효한 이메일 주소가 필요합니다.")
    structure=m.read(run/"structure_manifest.json")
    source_file=Path(structure.get("structure_file", ""))
    if not source_file.is_file() or sha256_file(source_file)!=structure.get("structure_sha256"):
        raise ValueError("제출 구조 파일 또는 SHA-256 검증에 실패했습니다.")
    raw=source_file.read_bytes()
    if b"V2000" not in raw[:500]:
        raise ValueError("PharmMapper는 MDL SDF V2000 구조 파일이 필요합니다.")
    prepared=sorted((run/"submissions").glob("PharmMapper_*.json"))
    if not prepared:
        raise ValueError("PharmMapper 작업 태그가 준비되지 않았습니다.")
    tag_doc=m.read(prepared[0])
    if tag_doc.get("submission_status") not in ("PREPARED_NOT_SUBMITTED","PENDING","SUBMITTED_RESPONSE_REVIEW_REQUIRED"):
        raise ValueError("PharmMapper 제출 상태를 다시 확인해야 합니다.")
    tag=tag_doc.get("compound_tag","")
    try:
        with source_file.open("rb") as handle:
            response=requests.post("https://www.lilab-ecust.cn/pharmmapper/submitjob.html", files={"file":(source_file.name,handle,"chemical/x-mdl-sdfile")}, data={"email":email,"describe":tag}, timeout=90)
        response.raise_for_status()
    except Exception as error:
        raise ValueError("PharmMapper 공식 제출 요청 실패: "+str(error)[:180])
    body=response.text
    job_match=re.search(r"(?<!\d)(\d{12})(?!\d)", body)
    job_id=job_match.group(1) if job_match else None
    ledger=m.read(run/"job_ledger.json")
    previous=ledger.get("pharmmapper_submission",{})
    attempts=list(previous.get("attempts",[]))
    attempts.append({"attempt":len(attempts)+1,"submitted_at_utc":m.now(),"job_id":job_id,"response_sha256":hashlib.sha256(body.encode("utf-8","replace")).hexdigest(),"email_stored":False})
    ledger["pharmmapper_submission"]={"provider":"PharmMapper","status":"SUBMITTED" if job_id else "SUBMITTED_RESPONSE_REVIEW_REQUIRED","job_id":job_id,"cid":structure.get("cid"),"input_sha256":structure.get("structure_sha256"),"compound_tag":tag,"submitted_at_utc":m.now(),"source_url":"https://www.lilab-ecust.cn/pharmmapper/submitjob.html","response_sha256":hashlib.sha256(body.encode("utf-8","replace")).hexdigest(),"email_stored":False,"attempts":attempts}
    m.save(run/"job_ledger.json",ledger)
    tag_doc["submission_status"]="SUBMITTED" if job_id else "SUBMITTED_RESPONSE_REVIEW_REQUIRED"
    tag_doc["job_id"]=job_id
    tag_doc["submitted_at_utc"]=m.now()
    m.save(prepared[0],tag_doc)
    progress=m.read(run/"analysis_progress.json")
    progress.update({"updated_at_utc":m.now(),"status":"PHARMMAPPER_SUBMITTED" if job_id else "PHARMMAPPER_SUBMISSION_RESPONSE_REVIEW_REQUIRED","pharmmapper_job_id":job_id,"pharmmapper_email_received_in_session":True,"external_submission_performed":True,"next_action":"SEA는 공식 사이트 CAPTCHA 완료 후 제출 필요" if job_id else "PharmMapper 응답에서 공식 작업 ID 확인 필요"})
    m.save(run/"analysis_progress.json",progress)
    return {"job_id":job_id,"status":progress["status"]}

def sea_copy_control(label, value):
    safe_value=h(value)
    return '<label>'+h(label)+' <input readonly value="'+safe_value+'"> <button type="button" data-copy="'+safe_value+'" onclick="navigator.clipboard.writeText(this.dataset.copy).then(()=>this.textContent='+"'복사됨'"+').catch(()=>alert('+"'복사에 실패했습니다. 입력값을 직접 선택해 복사하세요.'"+'))">복사</button></label>'

def role_status_panel(project):
    labels={"controller":"총괄","agent1":"화합물·질환 근거","agent2":"외부 표적 수집","agent3":"PPI·기능분석","agent4":"독립 QC","agent5":"결과 검토"}
    rows=[]
    for run_id in project.get("run_ids",[]):
        queue=m.read(WORKSPACE/"runs"/run_id/"work_queue.json")
        for task in queue.get("tasks",[]):
            rows.append('<tr><td>'+h(labels.get(task.get("agent"),task.get("agent","미지정")))+'</td><td>'+h(task.get("id"))+'</td><td>'+h(task.get("status","QUEUED"))+'</td><td>'+h(task.get("detail",task.get("info",{})))+'</td></tr>')
    if not rows: return '<section><h3>실행 역할 상태</h3><p class="muted">아직 생성된 작업 큐가 없습니다.</p></section>'
    return '<section><h3>실행 역할 상태</h3><p class="muted">표시는 역할명이 아니라 저장된 작업 큐의 실제 상태입니다. 자동 감시는 30분 간격으로 다음 외부 결과를 확인합니다.</p><table><tr><th>담당</th><th>작업</th><th>상태</th><th>상세</th></tr>'+''.join(rows)+'</table></section>'

def role_status_panel(project):
    labels={"controller":"총괄","agent1":"화합물·질환 근거","agent2":"외부 표적 수집","agent3":"PPI·기능분석","agent4":"독립 QC","agent5":"결과 검증"}
    done={"DONE","COMPLETED","COMPLETE","RETRIEVED","QC_PASSED"}
    active={"RUNNING","IN_PROGRESS","STARTED","SUBMITTED","QC_IN_PROGRESS"}
    errors={"ERROR","FAILED","NEEDS_ATTENTION","BLOCKED","RETRY_REQUIRED"}
    rows=[]; counts={"완료":0,"진행 중":0,"오류·보류":0,"시행 전":0}
    for run_id in project.get("run_ids",[]):
        run=WORKSPACE/"runs"/run_id
        request=m.read(run/"request.json")
        compound=request.get("compound_input",run_id)
        queue=m.read(run/"work_queue.json")
        tasks=list(queue.get("tasks",[]))
        progress=m.read(run/"analysis_progress.json")
        if progress:
            tasks.append({"agent":"controller","id":"analysis_progress","status":progress.get("status","NOT_STARTED"),"detail":progress.get("next_action","")})
        if not tasks:
            tasks=[{"agent":"controller","id":"run","status":"NOT_STARTED","detail":"분석 실행 전"}]
        for task in tasks:
            raw_status=str(task.get("status","NOT_STARTED")).upper()
            if raw_status in done or raw_status.endswith("_COMPLETE") or raw_status.endswith("_COMPLETED"): state="완료"; css="done"
            elif raw_status in active or "IN_PROGRESS" in raw_status or raw_status.endswith("_SUBMITTED"): state="진행 중"; css="active"
            elif raw_status in errors or "ERROR" in raw_status or "FAILED" in raw_status or "NEEDS_ATTENTION" in raw_status: state="오류·보류"; css="error"
            else: state="시행 전"; css="pending"
            counts[state]+=1
            detail=task.get("detail",task.get("info",{}))
            if isinstance(detail,(dict,list)): detail=json.dumps(detail,ensure_ascii=False)
            retry=' <a href="?project='+h(project.get("project_id"))+ '&run='+h(run_id)+'#decision-'+h(run_id)+'">상세·재작업</a>' if css=="error" else ''
            rows.append('<tr><td>'+h(labels.get(task.get("agent"),task.get("agent","미지정")))+'</td><td>'+h(compound)+'</td><td>'+h(task.get("id",""))+'</td><td><span class="state '+css+'">'+state+'</span><br><small>'+h(raw_status)+'</small></td><td>'+h(detail)+retry+'</td></tr>')
    summary=' · '.join(k+' '+str(v) for k,v in counts.items())
    if not rows: summary='시행 전 1'
    table='<table><tr><th>담당</th><th>화합물</th><th>단계</th><th>상태</th><th>다음 작업·오류</th></tr>'+''.join(rows)+'</table>'
    return '<section class="progress-overview"><details><summary><strong>전체 진행 상황</strong> · '+h(summary)+'</summary><p class="muted">총괄과 세부 에이전트의 현재 단계만 요약합니다. 오류·보류 항목은 상세·재작업 링크에서 다시 열 수 있습니다.</p><details><summary>상세 내역 표 보기</summary>'+table+'</details></details></section>'

def sea_result_state(run):
    row=m.read(Path(run)/"job_ledger.json").get("sea_submission", {})
    if row.get("raw_file") and Path(row["raw_file"]).is_file() and row.get("sha256")==sha256_file(row["raw_file"]): return "RETRIEVED",row
    return row.get("status","NOT_SUBMITTED"),row

def retrieve_sea_result(run):
    run=Path(run); ledger=m.read(run/"job_ledger.json"); row=ledger.get("sea_submission",{}); url=row.get("result_url") or row.get("source_url")
    if not url: raise ValueError("SEA 제출 작업 URL이 없습니다.")
    try:
        response=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=30); response.raise_for_status(); raw=response.content
        if len(raw)<100 or (b"Uniprot" not in raw and b"Target_Chembl_ID" not in raw): raise ValueError("검증 가능한 SEA 결과 원본 형식이 아닙니다.")
    except Exception as error:
        row.update({"status":"NEEDS_ATTENTION_DOWNLOAD_FAILED","last_checked_utc":m.now(),"last_error":"SEA result retrieval failed: "+str(error)[:180]}); ledger["sea_submission"]=row; m.save(run/"job_ledger.json",ledger)
        raise ValueError("SEA 결과 원본을 자동 회수하지 못했습니다. 원본과 SHA-256 없이는 완료로 사용하지 않습니다.")
    archive=run/"source_archive"/"SEA"; archive.mkdir(parents=True,exist_ok=True); digest=hashlib.sha256(raw).hexdigest(); target=archive/(str(row.get("job_id","sea"))+"_"+digest[:16]+".tsv")
    if not target.exists(): target.write_bytes(raw)
    row.update({"status":"RETRIEVED_UNVERIFIED","raw_file":str(target),"sha256":sha256_file(target),"retrieved_at_utc":m.now()}); ledger["sea_submission"]=row; m.save(run/"job_ledger.json",ledger)
    m.save(run/"sea_result_manifest.json",{"provider":"SEA","job_id":row.get("job_id"),"raw_file":str(target),"sha256":row["sha256"],"source_url":url,"downloaded_at_utc":m.now(),"qc_status":"UNVERIFIED"})
    return row

def external_submission_panel(project):
    cards=[]
    for run_id in project.get("run_ids",[]):
        run=WORKSPACE/"runs"/run_id; progress=m.read(run/"analysis_progress.json")
        if progress.get("status") not in ("LOCAL_PREPARATION_COMPLETE","SEA_SUBMITTED","SEA_RAW_RETRIEVED_QC_IN_PROGRESS","PHARMMAPPER_SUBMITTED","PHARMMAPPER_SUBMISSION_RESPONSE_REVIEW_REQUIRED"): continue
        request=m.read(run/"request.json"); ledger=m.read(run/"job_ledger.json"); sea_status,sea_ledger=sea_result_state(run); pharm=ledger.get("pharmmapper_submission",{})
        cid=request.get("compound_cid",""); smiles=request.get("compound_smiles",""); tag="NP-"+str(cid)+"-"+hashlib.sha256((str(cid)+str(smiles)).encode()).hexdigest()[:12]
        sea='<h4>SEA</h4>'
        if sea_status=="RETRIEVED": sea+='<p class="ok">SEA 원본 회수 완료 · SHA-256 '+h(sea_ledger.get("sha256"))+' · 독립 QC 대기</p>'
        elif sea_ledger.get("status")=="SUBMITTED": sea+='<p class="ok">SEA 자동 제출 확인됨 · 작업 ID '+h(sea_ledger.get("job_id"))+' · 결과 원본 회수 대기</p>'+form("/retrieve_sea",'<input type="hidden" name="run" value="'+h(run_id)+'">',"SEA 결과 원본 자동 회수 재시도")+'<p><a href="'+h(sea_ledger.get("source_url","https://sea.bkslab.org/"))+'" target="_blank" rel="noopener">SEA 결과 상태 열기</a></p>'
        elif sea_ledger.get("status")=="NEEDS_ATTENTION_DOWNLOAD_FAILED": sea+='<p class="warn">SEA 결과 원본 자동 회수 실패 — 원본·SHA-256 없이 완료 처리하지 않습니다.</p>'+form("/retrieve_sea",'<input type="hidden" name="run" value="'+h(run_id)+'">',"SEA 결과 원본 자동 회수 재시도")
        else: sea+='<p><a href="https://sea.bkslab.org/" target="_blank" rel="noopener">SEA 공식 제출 화면 열기</a></p>'+sea_copy_control("SEA SMILES",smiles)+sea_copy_control("PubChem CID",cid)+sea_copy_control("작업 태그",tag)+'<p class="warn">사람 확인(CAPTCHA)이 요구되면 완료 뒤에만 제출됩니다.</p>'
        pm='<h4>PharmMapper</h4>'
        if pharm.get("status") in ("SUBMITTED","SUBMITTED_RESPONSE_REVIEW_REQUIRED"): pm+='<p class="ok">PharmMapper 자동 제출 응답 확인됨'+(" · 작업 ID "+h(pharm.get("job_id")) if pharm.get("job_id") else " · 작업 ID 확인 대기")+' · 이메일 재입력 불필요</p>'
        else:
            fields='<input type="hidden" name="run" value="'+h(run_id)+'"><label>프로젝트 공용 PharmMapper 제출·결과 수신 이메일 (현재 세션 전용) <input type="email" name="pharmmapper_email" autocomplete="email" required placeholder="name@example.org"></label><p class="muted">최초 한 번만 입력하며 파일·로그·보고서에는 저장하지 않습니다.</p>'
            pm+=form("/submit_pharmmapper",fields,"PharmMapper 공식 제출")
        cards.append('<section><h4>'+h(request.get("compound_input"))+'</h4>'+sea+pm+'</section>')
    return '<section><h3>외부 표적 수집</h3><p class="muted">제출 확인과 결과 원본 회수는 구분합니다. 원본 파일과 SHA-256이 기록되어야 다음 분석으로 넘어갑니다.</p><p class="ok">다음 단계: 확보된 SEA 원본은 독립 종·UniProt QC로 자동 진행합니다. PharmMapper 원본이 확인되면 두 소스를 통합해 PPI 단계로 넘깁니다.</p>'+''.join(cards)+'</section>' if cards else ""

def begin_project_analysis(project):
    summaries=[]
    for run_id in project.get("run_ids", []):
        run=WORKSPACE/"runs"/run_id
        try:
            summary=begin_run_analysis(run)
            summaries.append({"run_id":run_id,"status":summary["status"],"next_action":summary["next_action"]})
        except Exception as error:
            summaries.append({"run_id":run_id,"status":"NEEDS_ATTENTION","next_action":str(error)})
    return summaries

def project_page(project_id, open_run_id="", notice=""):
    project=read_project(project_id)
    if not project: return layout('<section><p class="warn">프로젝트를 찾지 못했습니다.</p><p><a href="/">프로젝트 목록</a></p></section>')
    saved_runs=len(project.get("run_ids", []))
    content='<p><a href="/">프로젝트 목록</a></p>'
    if notice: content+='<section><p class="ok">'+h(notice)+'</p></section>'
    content+='<section><h3>'+h(project.get("name"))+'</h3><p class="muted">상태: '+h(project.get("status","DRAFT"))+' · 저장된 화합물 실행 '+str(saved_runs)+'건</p></section>'
    content+=role_status_panel(project)
    if saved_runs:
        zero_pending=[]; cards=[]; all_completed=True
        for index, run_id in enumerate(project.get("run_ids", [])):
            run=WORKSPACE/"runs"/run_id
            request=m.read(run/"request.json")
            if not request: continue
            approval=m.read(run/"initial_approval.json")
            review=m.read(run/"existing_data_review.json")
            candidate_count=len(review.get("candidates", []))
            if approval.get("user_approved") is not True: all_completed=False
            if candidate_count == 0 and approval.get("user_approved") is not True:
                zero_pending.append(run_id); continue
            state=decision_status(approval)
            detail_id='decision-'+run_id
            is_open=' open' if run_id == open_run_id else ''
            cards.append('<details id="'+h(detail_id)+'"'+is_open+'><summary><strong>'+h(request.get("compound_input"))+'</strong> · 확인 CID '+h(request.get("compound_cid","기록 없음"))+' · 기존 자료 후보 '+str(candidate_count)+'건 · '+h(state)+'</summary>'+run_panel(run, include_email=(index == 0 and "__shared__" not in SESSION_PHARMMAPPER_EMAIL))+'</details>')
        if zero_pending: content+=zero_candidate_form(project_id, zero_pending)
        content+='<section><h3>중간 저장된 화합물</h3>'+''.join(cards)+'</section>'
        progress=[]
        for run_id in project.get("run_ids", []):
            item=m.read(WORKSPACE/"runs"/run_id/"analysis_progress.json")
            if item:
                progress.append('<p><strong>'+h(run_id)+'</strong> · '+h(item.get("status"))+' · '+h(item.get("next_action"))+'</p>')
        if progress:
            content+='<section><h3>분석 실행 상태</h3>'+''.join(progress)+'</section>'
        if all_completed:
            external=external_submission_panel(project)
            if external:
                content+=external
            else:
                content+='<section><h3>분석 시작</h3><p class="muted">PubChem 구조 원본 저장, SHA-256 기록, 작업 태그 생성을 실행한 뒤 외부 제출 단계로 전환합니다.</p>'+form("/advance_project", '<input type="hidden" name="project" value="'+h(project_id)+'">', "분석 시작: 구조·작업 태그 준비")+'</section>'
    else:
        content+='<section><p class="muted">아직 저장된 화합물이 없습니다.</p></section>'
    content+='<section>'+new_compound_form(project_id)+'</section>'
    return layout(content)

def index():
    bits=['<p class="muted">새 프로젝트를 만들면 즉시 중간 저장됩니다. 이후 화합물·질환·CID·기존 자료 검토는 해당 프로젝트에 연결됩니다.</p>']
    bits.append('<section><h3>새 프로젝트</h3>'+form("/create_project", '<label>프로젝트명 <input name="project_name" placeholder="예: UC 두 화합물 분석"></label>', "새 프로젝트 만들기")+'</section>')
    bits.append('<h3>프로젝트 목록</h3>')
    projects=list_projects()
    if not projects: bits.append('<p class="muted">아직 저장된 프로젝트가 없습니다.</p>')
    for project in projects:
        url='/project?project='+quote(project["project_id"], safe="")
        bits.append('<section><h3><a href="'+h(url)+'">'+h(project.get("name"))+'</a></h3><p class="muted">상태: '+h(project.get("status","DRAFT"))+' · 저장된 화합물 실행 '+str(len(project.get("run_ids", [])))+'건</p><p><a href="'+h(url)+'">프로젝트 열기</a></p></section>')
    return layout(''.join(bits))

def confirmation(data, candidate_groups):
    rows=[]
    for group_index, (query, candidates) in enumerate(candidate_groups):
        for i, row in enumerate(candidates):
            label=f'CID {row["cid"]} | {row["title"]} | {row["formula"]} | {row["inchikey"]}'
            input_name=f"selected_cid_{group_index}"
            rows.append('<tr><td>'+h(query)+'</td><td><input type="radio" name="'+h(input_name)+'" value="'+h(row["cid"])+'" required '+("checked" if i==0 else "")+'></td><td>'+h(label)+'</td></tr>')
    fields='<input type="hidden" name="project" value="'+h(data.get("project", ""))+'"><input type="hidden" name="disease" value="'+h(data["disease"])+'"><input type="hidden" name="species" value="'+h(data["species"])+'"><table><tr><th>입력명</th><th>선택</th><th>PubChem 후보</th></tr>'+''.join(rows)+'</table>'
    return layout('<section><h3>2. CID 선택·확인</h3><p class="ok">각 화합물에서 선택한 CID로 구조 동일성을 고정한 뒤, 화합물별 기존 자료를 탐색합니다.</p>'+form("/new",fields,"선택 CID 전체를 등록하고 기존 자료 탐색")+'</section>')

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url=urlparse(self.path)
        if parsed_url.path=="/next":
            run_ids=parse_qs(parsed_url.query).get("run", [])
            run=WORKSPACE/"runs"/run_ids[0] if run_ids else None
            project=ensure_project_for_run(run) if run and (run/"request.json").exists() else None
            content=project_page(project["project_id"], open_run_id=run.name).encode() if project else layout('<section><p class="warn">프로젝트 실행을 찾지 못했습니다.</p><p><a href="/">프로젝트 목록</a></p></section>').encode()
        elif parsed_url.path=="/project":
            project_id=parse_qs(parsed_url.query).get("project", [""])[0]
            content=project_page(project_id).encode()
        elif parsed_url.path=="/decision":
            query=parse_qs(parsed_url.query)
            project_id=query.get("project", [""])[0]
            project=read_project(project_id)
            run_id=query.get("run", [""])[0]
            content=project_page(project_id, open_run_id=run_id).encode() if project and run_id in project.get("run_ids", []) else layout('<section><p class="warn">결정할 화합물을 찾지 못했습니다.</p><p><a href="/">프로젝트 목록</a></p></section>').encode()
        else:
            content=index().encode()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(content))); self.end_headers(); self.wfile.write(content)
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0"))
        if n>10000: self.send_error(413); return
        parsed=parse_qs(self.rfile.read(n).decode())
        data={k:v[0] for k,v in parsed.items()}
        if data.get("token")!=TOKEN: self.send_error(403); return
        target=urlparse(self.path).path
        if target=="/create_project":
            project=create_project(data.get("project_name", ""))
            content=project_page(project["project_id"]).encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
        if target=="/advance_project":
            project=read_project(data.get("project", ""))
            if not project: raise ValueError("프로젝트를 찾지 못했습니다.")
            pending=[run_id for run_id in project.get("run_ids", []) if m.read(WORKSPACE/"runs"/run_id/"initial_approval.json").get("user_approved") is not True]
            if pending: raise ValueError("모든 화합물의 분석 경로를 확정한 뒤 진행할 수 있습니다.")
            summaries=begin_project_analysis(project)
            failed=[item for item in summaries if item["status"]!="LOCAL_PREPARATION_COMPLETE"]
            project["status"]="ANALYSIS_NEEDS_ATTENTION" if failed else "ANALYSIS_PREPARED"
            project["updated_at_utc"]=m.now(); save_project(project)
            detail=" / ".join(item["run_id"]+": "+item["next_action"] for item in summaries)
            notice=("로컬 분석 준비를 완료했습니다. "+detail) if not failed else ("일부 화합물의 분석 준비가 멈췄습니다. "+detail)
            content=project_page(project["project_id"], notice=notice).encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
        if target=="/retrieve_sea":
            run_id=data.get("run",""); run=WORKSPACE/"runs"/run_id
            try:
                if not run_id or Path(run_id).name!=run_id or not (run/"request.json").exists(): raise ValueError("유효하지 않은 실행")
                retrieve_sea_result(run); project=ensure_project_for_run(run); content=project_page(project["project_id"],notice="SEA 결과 원본을 보존했습니다. SHA-256 기록 뒤 독립 QC를 진행합니다.").encode()
            except Exception as error:
                project=ensure_project_for_run(run) if (run/"request.json").exists() else None; content=(project_page(project["project_id"],notice="SEA 원본 회수 중단: "+str(error)) if project else layout('<section><p class="warn">SEA 원본 회수 중단: '+h(str(error))+'</p></section>')).encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
        if target=="/submit_pharmmapper":
            run_id=data.get("run","")
            if not run_id or Path(run_id).name!=run_id: raise ValueError("유효하지 않은 실행")
            run=WORKSPACE/"runs"/run_id
            if not (run/"request.json").exists(): raise ValueError("실행을 찾을 수 없습니다")
            project=ensure_project_for_run(run)
            existing=m.read(run/"job_ledger.json").get("pharmmapper_submission", {})
            if existing.get("status") in ("SUBMITTED","SUBMITTED_RESPONSE_REVIEW_REQUIRED"):
                content=project_page(project["project_id"],notice="PharmMapper 제출 응답이 이미 기록되어 이메일 재입력과 중복 제출을 건너뛰었습니다.").encode()
                self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
            try:
                result=submit_pharmmapper(run,data.get("pharmmapper_email","").strip())
            except Exception as error:
                content=project_page(project["project_id"],notice="PharmMapper 제출 중단: "+str(error)).encode()
                self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
            project["status"]="EXTERNAL_SUBMISSION_IN_PROGRESS"
            project["updated_at_utc"]=m.now(); save_project(project)
            message="PharmMapper 공식 제출 완료: 작업 ID "+str(result["job_id"]) if result.get("job_id") else "PharmMapper 제출 응답을 받았으나 작업 ID 확인이 필요합니다."
            content=project_page(project["project_id"],notice=message).encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
        if target=="/approve_zero":
            project=read_project(data.get("project", ""))
            run_ids=[run_id for run_id in data.get("run_ids", "").split(",") if run_id]
            if not project or not run_ids or any(run_id not in project.get("run_ids", []) for run_id in run_ids): raise ValueError("유효하지 않은 신규 제출 승인입니다.")
            submitted_email=data.get("pharmmapper_email", "").strip()
            if submitted_email: SESSION_PHARMMAPPER_EMAIL["__shared__"]=submitted_email
            for run_id in run_ids:
                run=WORKSPACE/"runs"/run_id; review=m.read(run/"existing_data_review.json")
                if review.get("candidates", []): raise ValueError("기존 자료가 있는 화합물은 간편 승인으로 처리할 수 없습니다.")
                approval={"user_approved":True,"approved_at_utc":m.now(),"reuse_policy":"NOT_APPLICABLE","supplement_authorized":False,"new_submission_authorized":data.get("new_submit")=="yes","email_notification_authorized":data.get("email_notify")=="yes","pharmmapper_session_email_provided":"__shared__" in SESSION_PHARMMAPPER_EMAIL,"reviewed_candidates":0,"analysis_path":"NEW_SUBMISSION_ONLY","limitations":"Scientific QC, provider terms, login, CAPTCHA, and external submission gates remain mandatory. PharmMapper email is session-only and never stored in this file."}
                m.save(run/"initial_approval.json", approval)
            project["status"]="DECISIONS_IN_PROGRESS"; project["updated_at_utc"]=m.now(); save_project(project)
            content=project_page(project["project_id"], notice="기존 자료 0건 화합물의 신규 제출 경로를 저장했습니다.").encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
        if target=="/resolve":
            queries=compound_queries(data.get("compound",""))
            candidate_groups=[(query, cid_candidates(query)) for query in queries]
            unresolved=[query for query, rows in candidate_groups if not rows]
            if not queries:
                content=layout('<section><h3>화합물을 입력하세요</h3><p class="warn">한 줄에 하나씩 화합물명 또는 CID를 입력해야 합니다.</p><p><a href="/">돌아가기</a></p></section>').encode()
            elif unresolved:
                content=layout('<section><h3>CID 후보를 찾지 못한 화합물이 있습니다</h3><p class="warn">'+h(', '.join(unresolved))+'</p><p>정확한 PubChem CID를 입력하거나 화합물명 철자·동의어를 확인한 뒤 다시 시도하세요. 모든 화합물의 CID를 확인하기 전에는 등록하지 않습니다.</p><p><a href="/">돌아가기</a></p></section>').encode()
            else:
                content=confirmation(data,candidate_groups).encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
        msg="처리 완료"
        try:
            if target=="/new":
                import np_agent_queue as q
                project_id=data.get("project", "")
                project=read_project(project_id)
                if not project: raise ValueError("프로젝트를 먼저 만들거나 선택하세요.")
                cids=[value.strip() for key, value in sorted(data.items()) if key.startswith("selected_cid_") and value.strip()]
                if not cids: raise ValueError("선택한 CID가 없습니다.")
                project_runs=[WORKSPACE/"runs"/run_id for run_id in project.get("run_ids", []) if (WORKSPACE/"runs"/run_id/"request.json").exists()]
                registered=[]; duplicates=[]; run_ids=[]
                for cid in cids:
                    rows=cid_candidates("CID "+cid)
                    if not rows: raise ValueError(f"CID {cid}를 PubChem에서 다시 확인하지 못했습니다.")
                    row=rows[0]; compound=f'{row["title"]} (CID {cid})'
                    duplicate=next((a for a in project_runs if (lambda x: str(x.get("compound_cid",""))==cid and x.get("disease_input","").casefold()==data.get("disease","").casefold() and x.get("species")==data.get("species","Homo sapiens"))(m.read(a/"request.json"))),None)
                    if duplicate:
                        duplicates.append(cid); run_ids.append(duplicate.name); continue
                    home=q.initialize(WORKSPACE,compound,data.get("disease",""),data.get("species","Homo sapiens"))
                    req=m.read(home/"request.json"); req.update({"project_id":project_id,"compound_cid":cid,"compound_title":row["title"],"compound_iupac":row["iupac"],"compound_formula":row["formula"],"compound_inchikey":row["inchikey"],"compound_smiles":row["smiles"],"identity_source":"PubChem PUG REST","identity_confirmed_utc":m.now()}); m.save(home/"request.json",req)
                    m.review(home)
                    review=m.read(home/"existing_data_review.json")
                    registered.append(f'CID {cid}: 기존 자료 후보 {len(review.get("candidates",[]))}건')
                    project_runs.append(home); run_ids.append(home.name)
                parts=[]
                if registered: parts.append(f'{len(registered)}개 화합물 등록·탐색 완료 — ' + '; '.join(registered))
                if duplicates: parts.append('이미 같은 CID·질환·종으로 등록됨: ' + ', '.join(duplicates))
                project["run_ids"]=list(dict.fromkeys(project.get("run_ids", [])+run_ids))
                project["status"]="RUNS_CREATED"
                project["updated_at_utc"]=m.now()
                save_project(project)
                msg=' / '.join(parts)+'. 프로젝트에서 기존 자료 검토 또는 신규 제출 간편 승인을 진행하세요.'
                content=project_page(project_id, notice=msg).encode()
                self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
            else:
                run_id=data.get("run","")
                if not run_id or Path(run_id).name!=run_id: raise ValueError("유효하지 않은 실행")
                run=WORKSPACE/"runs"/run_id
                if not (run/"request.json").exists(): raise ValueError("실행을 찾을 수 없습니다")
                if target=="/reopen_decision":
                    approval=m.read(run/"initial_approval.json")
                    approval["user_approved"]=False
                    approval["reopened_at_utc"]=m.now()
                    approval["reopened_from_analysis_path"]=approval.get("analysis_path")
                    m.save(run/"initial_approval.json", approval)
                    project=ensure_project_for_run(run)
                    content=project_page(project["project_id"], open_run_id=run.name, notice="재결정을 위해 이 화합물의 카드를 펼쳤습니다.").encode()
                    self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
                if target=="/scan":
                    m.review(run)
                    project=ensure_project_for_run(run)
                    content=project_page(project["project_id"], open_run_id=run.name, notice="기존 자료 탐색을 갱신했습니다.").encode()
                    self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
                elif target=="/approve":
                    submitted_email=data.get("pharmmapper_email","").strip()
                    if submitted_email:
                        SESSION_PHARMMAPPER_EMAIL["__shared__"]=submitted_email
                        SESSION_PHARMMAPPER_EMAIL[run.name]=submitted_email
                    review=m.read(run/"existing_data_review.json")
                    candidate_count=len(review.get("candidates", []))
                    no_existing_data=(candidate_count == 0)
                    approval={"user_approved":True,"approved_at_utc":m.now(),"reuse_policy":"NOT_APPLICABLE" if no_existing_data else data.get("reuse","REVIEW_EACH"),"supplement_authorized":False if no_existing_data else data.get("supplement")=="yes","new_submission_authorized":data.get("new_submit")=="yes" if no_existing_data else data.get("supplement")=="yes","email_notification_authorized":data.get("email_notify")=="yes","pharmmapper_session_email_provided":"__shared__" in SESSION_PHARMMAPPER_EMAIL,"reviewed_candidates":candidate_count,"analysis_path":"NEW_SUBMISSION_ONLY" if no_existing_data else "EXISTING_REVIEW_WITH_OPTIONAL_SUPPLEMENT","limitations":"Scientific QC, provider terms, login, CAPTCHA, and external submission gates remain mandatory. PharmMapper email is session-only and never stored in this file."}
                    m.save(run/"initial_approval.json",approval)
                    project=ensure_project_for_run(run)
                    project["status"]="DECISIONS_IN_PROGRESS"
                    project["updated_at_utc"]=m.now()
                    save_project(project)
                    next_run=next_unapproved_run(project, run.name)
                    notice="분석 경로를 저장했습니다. 다음 미결정 화합물을 펼쳤습니다." if next_run else "분석 경로를 저장했습니다. 모든 화합물 결정이 완료되었습니다."
                    content=project_page(project["project_id"], open_run_id=next_run or "", notice=notice).encode()
                    self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content); return
                else: raise ValueError("지원하지 않는 동작")
        except Exception as e:
            msg="처리하지 못했습니다: "+str(e)
        content=layout('<section><p>'+h(msg)+'</p><p><a href="/">돌아가기</a></p></section>').encode()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(content)

if __name__=="__main__":
    WORKSPACE.mkdir(parents=True,exist_ok=True)
    print("LOCAL_DASHBOARD http://127.0.0.1:8765",flush=True)
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
