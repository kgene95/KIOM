from __future__ import annotations
import json, re, shutil, traceback, subprocess, tempfile
from datetime import datetime
from pathlib import Path
import streamlit as st
import core as _core
import importlib
importlib.reload(_core)
from core import *
import providers
importlib.reload(providers)

st.set_page_config(page_title="KIOM NP Workbench",page_icon="🧬",layout="wide")
if "lang" not in st.session_state: st.session_state.lang="한국어"
if "project" not in st.session_state: st.session_state.project=None
if "page" not in st.session_state: st.session_state.page="분석 설정"
lang=st.sidebar.selectbox("Language / 언어",["한국어","English"],key="lang")
KO=lang=="한국어"
def T(kr,en): return kr if KO else en

st.title("KIOM Network Pharmacology Workbench")
st.caption(T("연구용 로컬 분석 워크벤치 · 출처와 QC를 보존합니다","Local research workbench · source- and QC-traceable"))

with st.sidebar:
    st.subheader(T("프로젝트 저장","Project storage"))
    root=Path(st.text_input(T("프로젝트 폴더","Project folder"),str(Path.home()/"KIOM_NP_Projects"))).expanduser()
    hidden_projects_path=root/"00_drafts/hidden_projects.json"
    hidden_projects=set(load_json(hidden_projects_path,[]) or [])
    all_projects=sorted([p for p in root.glob("*") if p.is_dir() and (p/"00_project/NP_manifest.json").exists()],key=lambda p:p.stat().st_mtime,reverse=True) if root.exists() else []
    projects=[p for p in all_projects if p.name not in hidden_projects]
    if not projects and all_projects:
        # Never leave the user with an empty selector when real project folders
        # exist. Show the two most recently modified projects as a recoverable
        # fallback; the hidden list itself remains unchanged until the user
        # explicitly restores a project.
        projects=all_projects[:2]
        st.warning(T("모든 프로젝트가 숨김 처리되어 최근 프로젝트 2개를 임시 표시합니다.","All projects are hidden; showing the two most recent projects as a recovery view."))
    labels=[p.name for p in projects]
    if labels:
        def open_selected_project_from_list():
            selected_name=st.session_state.get("existing_project_choice")
            if selected_name:
                st.session_state.project=str(root/selected_name)
                st.session_state.page="프로젝트"
                st.session_state.nav="프로젝트" if KO else "Project"
        chosen=st.selectbox(T("기존 프로젝트 열기","Open existing project"),labels,index=labels.index(Path(st.session_state.project).name) if st.session_state.project and Path(st.session_state.project).name in labels else 0,key="existing_project_choice",on_change=open_selected_project_from_list)
        if st.session_state.page=="프로젝트" and not st.session_state.project:
            st.session_state.project=str(root/chosen)
        open_col,remove_col=st.columns([5,1])
        if open_col.button(T("열기","Open"),help=T("선택한 프로젝트를 엽니다.","Open the selected project.")):
            st.session_state.project=str(root/chosen); st.session_state.page="프로젝트"; st.session_state.nav="프로젝트" if KO else "Project"; st.rerun()
        if remove_col.button("✕",key="remove_project_from_list",help=T("선택한 프로젝트를 목록에서만 제거합니다. 폴더와 분석 결과는 삭제하지 않습니다.","Remove the selected project from this list only. The folder and analysis results are not deleted.")):
            save_json(hidden_projects_path,sorted(hidden_projects|{chosen}))
            if st.session_state.project and Path(st.session_state.project).name==chosen: st.session_state.project=None
            st.rerun()
    if hidden_projects:
        st.caption(T(f"목록에서 숨긴 프로젝트: {len(hidden_projects)}개 · ‘프로젝트 관리’에서 다시 표시하거나 완전 삭제할 수 있습니다.",f"Hidden projects: {len(hidden_projects)} · restore or permanently delete them in Project management."))
        hidden_choices=[name for name in sorted(hidden_projects) if any(p.name==name for p in all_projects)]
        if hidden_choices:
            restore_name=st.selectbox(T("숨긴 프로젝트 복원","Restore hidden project"),hidden_choices,key="restore_hidden_project")
            if st.button(T("선택 프로젝트 다시 표시","Show selected project"),key="restore_hidden_project_button"):
                save_json(hidden_projects_path,sorted(hidden_projects-{restore_name})); st.rerun()
    st.caption(T("앱 설정과 현재 입력은 저장 경로의 00_drafts에 자동 저장됩니다.","App settings and current form inputs are autosaved under 00_drafts."))
    page_names=["분석 설정","프로젝트","프로젝트 관리","Transcriptomics","범위 및 도움말"] if KO else ["Analysis setup","Project","Project management","Transcriptomics","Scope & help"]
    keymap=dict(zip(page_names,["분석 설정","프로젝트","프로젝트 관리","Transcriptomics","범위 및 도움말"]))
    desired_label=next((label for label,internal in keymap.items() if internal==st.session_state.page),page_names[0])
    if st.session_state.get("nav")!=desired_label: st.session_state.nav=desired_label
    current_idx=list(keymap.values()).index(st.session_state.page) if st.session_state.page in keymap.values() else 0
    sel=st.radio(T("페이지","Page"),page_names,index=current_idx,key="nav",on_change=lambda:setattr(st.session_state,"page",keymap[st.session_state.nav]))
    st.info(T("분석 실행은 이 PC의 Python 프로세스에서 수행됩니다. API 연결에는 인터넷이 필요합니다.","Analysis runs in this PC's Python process. API modules require internet access."))

# Root-level autosaved draft survives browser/server restart. This stores inputs, not uploaded data.
draft_path=root/"00_drafts/np_draft.json"
if "draft_loaded" not in st.session_state:
    d=load_json(draft_path,{}) or {}
    for k,v in d.items():
        if k not in st.session_state: st.session_state[k]=v
    st.session_state.draft_loaded=True

def save_draft():
    keys=["compound_q","disease_q","compound_record","compound_records","disease_record","disease_records","analysis_mode","analysis_strategy","transcriptomics_choice"]
    save_json(draft_path,{k:st.session_state.get(k) for k in keys})

def set_project(p):
    st.session_state.project=str(p); st.session_state.page="프로젝트"; st.session_state.nav="프로젝트" if KO else "Project"

def reset_compound_candidates():
    st.session_state.pop("compound_hits",None)
    save_draft()

def reset_disease_candidates():
    st.session_state.pop("disease_hits",None)
    save_draft()

@st.cache_data(ttl=3600,show_spinner=False)
def cached_compound_suggestions(q): return providers.pubchem_suggestions(q)

@st.cache_data(ttl=3600,show_spinner=False)
def cached_compound_lookup(q): return providers.pubchem_compound(q)

@st.cache_data(ttl=3600,show_spinner=False)
def cached_disease_lookup(q): return providers.ols_disease(q)

def search_compound_on_enter():
    q=(st.session_state.get("compound_q") or "").strip()
    st.session_state.pop("compound_hits",None)
    if q:
        try: st.session_state.compound_hits=providers.pubchem_compound(q)
        except Exception as e: st.session_state.compound_search_error=str(e)
    st.session_state.pop("compound_search_error",None) if not q else None

def search_disease_on_enter():
    q=(st.session_state.get("disease_q") or "").strip()
    st.session_state.pop("disease_hits",None)
    if q:
        try: st.session_state.disease_hits=providers.ols_disease(q)
        except Exception as e: st.session_state.disease_search_error=str(e)
    st.session_state.pop("disease_search_error",None) if not q else None

if st.session_state.page=="분석 설정":
    st.header(T("새 NP 프로젝트","New NP project"))
    st.caption(T("이 화면의 입력은 새로고침 후에도 자동 저장됩니다. 새 분석을 시작하려면 아래 초기화 버튼을 사용하세요.","Entries on this page are autosaved across refreshes. Use the reset button below to start a new analysis."))
    if st.button(T("새 입력 목록으로 초기화","Clear confirmed compounds and diseases"),type="secondary",help=T("현재 화면의 화합물·질환 검색어, 확정 목록, 검색 후보만 지웁니다. 이미 생성한 프로젝트 폴더와 분석 결과는 삭제하지 않습니다.","Clears only this page's queries, confirmed lists, and search candidates. Existing project folders and results are not deleted.")):
        for key in ["compound_q","disease_q","compound_record","compound_records","disease_record","disease_records","compound_hits","disease_hits"]:
            st.session_state.pop(key,None)
        st.session_state["analysis_strategy"]="current_de_novo"
        st.session_state.pop("settings_contact_email",None)
        st.session_state.pop("settings_email_consent",None)
        save_draft()
        st.rerun()
    left,right=st.columns(2)
    with left:
        st.subheader(T("화합물 식별","Resolve compound"))
        cq=st.text_input(T("화합물명, 동의어 또는 CID","Compound name, synonym, or CID"),key="compound_q",on_change=search_compound_on_enter,placeholder="naringenin or CID 439246",help=T("입력 후 Enter를 누르면 PubChem 후보를 조회합니다. CID 439246처럼 직접 입력할 수도 있습니다.","Press Enter to search PubChem. You can also enter a CID such as CID 439246."))
        # Numeric CID input is resolved immediately as a fallback for browsers that
        # do not fire text_input's on_change event when Enter is pressed.
        cid_candidate=cq.strip().replace("CID","",1).replace("cid","",1).replace(":","").strip()
        if cid_candidate.isdigit() and not st.session_state.get("compound_hits"):
            try: st.session_state.compound_hits=cached_compound_lookup(cid_candidate)
            except Exception as e: st.session_state.compound_search_error=str(e)
        if "compound_records" not in st.session_state: st.session_state.compound_records=[]
        if not st.session_state.compound_records and st.session_state.get("compound_record"): st.session_state.compound_records=[st.session_state.compound_record]
        if st.button(T("PubChem에서 후보 불러오기","Fetch PubChem records"),key="pubchem_search") and cq.strip():
            try: st.session_state.pop("compound_search_error",None); st.session_state.compound_hits=providers.pubchem_compound(cq)
            except Exception as e: st.error(T(f"PubChem 조회 실패: {e}",f"PubChem lookup failed: {e}"))
        if st.session_state.get("compound_search_error"): st.error(T(f"PubChem 조회 실패: {st.session_state.compound_search_error}",f"PubChem lookup failed: {st.session_state.compound_search_error}"))
        hits=st.session_state.get("compound_hits",[])
        if hits:
            labels=[f"CID {x.get('CID')} | {x.get('IUPACName','')} | {x.get('MolecularFormula','')} | {x.get('InChIKey','')}" for x in hits]
            ix=st.selectbox(T("정확한 구조 확인","Select exact structure"),range(len(hits)),format_func=lambda i:labels[i])
            if st.button(T("화합물 목록에 추가","Add compound to list")):
                x=hits[ix]; cid=x.get("CID"); display_name=cq.strip()
                if cid:
                    try:
                        synonyms=providers.pubchem_synonyms(cid)
                        named=[s for s in synonyms if any(ch.isalpha() for ch in s) and not s.startswith(("CHEMBL","CHEBI:","DTX","SCHEMBL","MFCD","AKOS"))]
                        preferred=[s for s in named if "vitexin" in s.lower() or "naringenin" in s.lower()]
                        if preferred: named=preferred
                        if named: display_name=named[0]
                    except Exception: pass
                record={"name":display_name,"query":cq.strip(),"pubchem_cid":cid,"iupac_name":x.get("IUPACName"),"formula":x.get("MolecularFormula"),"canonical_smiles":x.get("ConnectivitySMILES") or x.get("CanonicalSMILES"),"isomeric_smiles":x.get("SMILES") or x.get("IsomericSMILES"),"inchikey":x.get("InChIKey"),"source":"PubChem PUG REST","retrieved_utc":now()}
                existing={str(r.get("pubchem_cid")) for r in st.session_state.compound_records}
                if str(record["pubchem_cid"]) not in existing: st.session_state.compound_records.append(record)
                st.session_state.compound_record=st.session_state.compound_records[0]; save_draft()
        if st.session_state.compound_records:
            st.success(T(f"확정 화합물 {len(st.session_state.compound_records)}개",f"Confirmed compounds: {len(st.session_state.compound_records)}"))
            st.dataframe([{ "name":r.get("name"),"PubChem CID":r.get("pubchem_cid"),"formula":r.get("formula")} for r in st.session_state.compound_records],hide_index=True,width="stretch")
            compound_remove_indices=list(range(len(st.session_state.compound_records)))
            remove_compound_index=st.selectbox(T("목록에서 제거할 화합물","Remove a confirmed compound"),compound_remove_indices,format_func=lambda i:f"{st.session_state.compound_records[i].get('name')} · CID {st.session_state.compound_records[i].get('pubchem_cid')}",key="remove_compound_choice")
            if st.button(T("선택 화합물 목록에서 제거","Remove selected compound"),key="remove_compound_button"):
                st.session_state.compound_records.pop(remove_compound_index)
                st.session_state.compound_record=st.session_state.compound_records[0] if st.session_state.compound_records else None
                save_draft(); st.rerun()
    with right:
        st.subheader(T("질환 개념 확인","Resolve disease concept"))
        dq=st.text_input(T("질환명 또는 ontology ID","Disease name or ontology ID"),key="disease_q",on_change=search_disease_on_enter,placeholder="ulcerative colitis or MONDO:0005101",help=T("입력 후 Enter를 누르면 EBI OLS 후보를 조회합니다.","Press Enter to search EBI OLS."))
        # Resolve disease names and ontology IDs automatically even when a browser
        # does not submit the text_input on Enter.
        if len(dq.strip()) >= 3 and not st.session_state.get("disease_hits"):
            try: st.session_state.disease_hits=cached_disease_lookup(dq.strip())
            except Exception as e: st.session_state.disease_search_error=str(e)
        if "disease_records" not in st.session_state: st.session_state.disease_records=[]
        if not st.session_state.disease_records and st.session_state.get("disease_record"): st.session_state.disease_records=[st.session_state.disease_record]
        if st.button(T("EBI OLS에서 후보 불러오기","Fetch EBI OLS concepts"),key="ols_search") and dq.strip():
            try: st.session_state.pop("disease_search_error",None); st.session_state.disease_hits=providers.ols_disease(dq)
            except Exception as e: st.error(T(f"OLS 조회 실패: {e}",f"OLS lookup failed: {e}"))
        if st.session_state.get("disease_search_error"): st.error(T(f"OLS 조회 실패: {st.session_state.disease_search_error}",f"OLS lookup failed: {st.session_state.disease_search_error}"))
        dh=st.session_state.get("disease_hits",[])
        if dh:
            dl=[f"{x.get('label')} | {x.get('ontology_name')} | {x.get('obo_id') or x.get('short_form')}" for x in dh]
            di=st.selectbox(T("질환 개념 선택","Select disease concept"),range(len(dh)),format_func=lambda i:dl[i])
            if st.button(T("질환 목록에 추가","Add disease to list")):
                x=dh[di]; record={"name":x.get("label",dq),"query":dq,"ontology":x.get("ontology_name"),"ontology_id":x.get("obo_id") or x.get("short_form"),"iri":x.get("iri"),"source":"EBI OLS4","retrieved_utc":now()}
                existing={str(r.get("ontology_id")) for r in st.session_state.disease_records}
                if str(record["ontology_id"]) not in existing: st.session_state.disease_records.append(record)
                st.session_state.disease_record=st.session_state.disease_records[0]; save_draft()
        if st.session_state.disease_records:
            st.success(T(f"확정 질환 {len(st.session_state.disease_records)}개",f"Confirmed diseases: {len(st.session_state.disease_records)}"))
            st.caption(T("질환들은 하나로 합치지 않습니다. 프로젝트 생성 시 질환별 독립 프로젝트가 생성됩니다.","Diseases are not merged. Creating projects makes one independent project per disease."))
            st.dataframe([{ "name":r.get("name"),"ontology":r.get("ontology"),"ontology_id":r.get("ontology_id")} for r in st.session_state.disease_records],hide_index=True,width="stretch")
            disease_remove_indices=list(range(len(st.session_state.disease_records)))
            remove_disease_index=st.selectbox(T("목록에서 제거할 질환","Remove a confirmed disease"),disease_remove_indices,format_func=lambda i:f"{st.session_state.disease_records[i].get('name')} · {st.session_state.disease_records[i].get('ontology_id')}",key="remove_disease_choice")
            if st.button(T("선택 질환 목록에서 제거","Remove selected disease"),key="remove_disease_button"):
                st.session_state.disease_records.pop(remove_disease_index)
                st.session_state.disease_record=st.session_state.disease_records[0] if st.session_state.disease_records else None
                save_draft(); st.rerun()
    st.divider()
    mode=st.radio(T("분석 모드","Analysis mode"),["Publication","Screening","Custom"],horizontal=True,key="analysis_mode")
    if "analysis_strategy" not in st.session_state:
        st.session_state.analysis_strategy="current_de_novo"
    strategy=st.radio(T("NP 분석 출처 전략","NP source strategy"),["current_de_novo","CMPE_reproduction","replacement_proxy"],format_func=lambda x:{"current_de_novo":"최신 독립분석","CMPE_reproduction":"원고 재현","replacement_proxy":"대체 출처 민감도"}[x],horizontal=True,key="analysis_strategy")
    st.caption(T("원고는 독립분석 결과를 개인적으로 비교하는 참고 기준입니다. 원고 재현은 동일한 원자료와 파라미터를 확보했을 때만 선택하세요.","The manuscript is a reference for personal comparison. Select manuscript reproduction only when the same raw sources and parameters are available."))
    st.session_state.contact_email=st.text_input(T("외부 서비스용 이메일(선택)","Email for external services (optional)"),value=st.session_state.get("contact_email",""),key="settings_contact_email",placeholder="name@example.org")
    st.session_state.email_submission_consent=st.checkbox(T("외부 서비스 제출·메일 확인을 직접 승인했습니다.","I will personally approve external submissions and check result emails."),value=st.session_state.get("email_submission_consent",False),key="settings_email_consent")
    st.caption(T("이메일은 외부 사이트 제출 안내에만 사용하며 manifest·분석 결과에는 저장하지 않습니다. 앱이 Gmail을 자동 열람하거나 외부 사이트에 대신 제출하지 않습니다.","Email is used only for external-site guidance and is not saved in the manifest or analysis results. The app does not read Gmail or submit to external sites."))
    if strategy=="CMPE_reproduction":
        st.warning(T("원고 재현 모드: 원고와 동일한 출처의 공식 원자료를 업로드해야 합니다. 자료가 없으면 원고 수치를 재현했다고 표시하지 않습니다.","Manuscript reproduction: upload official raw exports from the manuscript sources. Missing raw data will not be labelled reproduced."))
    elif strategy=="replacement_proxy":
        st.info(T("대체 출처 모드: 원고와 다른 데이터베이스를 사용한 proxy/sensitivity 결과로만 표시합니다.","Replacement-source mode: results are labelled proxy/sensitivity and are not merged with the manuscript branch."))
    save_draft()
    st.markdown(T("표적 예측 자료원은 검색 결과를 자동으로 긁어오지 않습니다. 허용된 API가 없거나 약관이 불명확한 출처는 원본 CSV를 업로드해 출처·점수와 함께 기록합니다.","Target predictor sites are not silently scraped. Sources without an approved API or clear terms are supplied as raw CSV exports with score and provenance."))
    if st.button(T("프로젝트 생성","Create project"),type="primary",disabled=not(st.session_state.get("compound_records") and st.session_state.get("disease_records"))):
        created=[create_project(root,st.session_state.compound_records,disease,mode,st.session_state.get("analysis_strategy","current_de_novo")) for disease in st.session_state.disease_records]
        st.session_state.created_projects=[str(x) for x in created]
        set_project(created[0]); st.rerun()

elif st.session_state.page=="프로젝트":
    if not st.session_state.project or not Path(st.session_state.project).exists(): st.info(T("프로젝트를 생성하거나 왼쪽에서 기존 프로젝트를 여세요.","Create a project or open one from the sidebar."))
    else:
        p=Path(st.session_state.project); manifest=load_json(p/"00_project/NP_manifest.json",{}); cp=load_json(p/"00_project/NP_checkpoint.json",{})
        st.header(p.name); st.caption(str(p)); st.info(f"{T('현재 단계','Current stage')}: {cp.get('stage','—')} · {T('상태','Status')}: {cp.get('status','—')}")
        with st.expander(T("분석 흐름 / 수행 가능성","Workflow / implementation status"),expanded=False):
            st.markdown(T("""
1. **입력 방식 선택 (현재 화면)**: 자동 수집 또는 원자료 입력을 선택합니다.
2. **표적 근거 수집**: 자동 수집은 PubChem/Open Targets를 사용합니다. 원자료 입력을 선택하면 SwissTargetPrediction·SEA·PharmMapper 안내와 GPT 지시문이 바로 나타납니다.
3. **사람 유전자 ID/QC 및 overlap**: source별 원자료를 보존한 뒤 사람 유전자 매핑과 공통 표적을 계산합니다.
4. **STRING·enrichment·Cytoscape 내보내기**: QC를 통과한 overlap만 네트워크와 enrichment에 사용합니다.
5. **검토·보강**: 공통 표적이 없거나 결과가 부족하면 이 단계로 돌아와 source를 추가한 뒤 다시 실행합니다.
""","""
1. **Choose input mode (current screen)**: select automatic collection or source-file upload.
2. **Collect target evidence**: automatic mode uses PubChem/Open Targets. Upload mode immediately shows SwissTargetPrediction/SEA/PharmMapper guidance and a GPT prompt.
3. **Human gene ID/QC and overlap**: preserve source files, map human genes, and calculate common targets.
4. **STRING, enrichment, and Cytoscape export**: only QC-passed overlap enters network and enrichment.
5. **Review and supplement**: if overlap is absent or evidence is incomplete, return to step 2, add sources, and rerun.
"""))
            st.warning(T("자동 수집은 PubChem 활성 bioassay와 Open Targets 질환 연관을 출발점으로 사용합니다. SwissTargetPrediction/PharmMapper/SEA와 라이선스 자료원은 사용자가 내려받은 원자료를 추가하세요. 웹 폼 자동 스크래핑은 하지 않습니다.","Automatic collection uses active PubChem bioassays and Open Targets disease associations as a starting point. Add user-exported sources for SwissTargetPrediction/PharmMapper/SEA and licensed resources. No web-form scraping is run."))
        st.subheader(T("1) 분석 입력 방식 선택 — 표적 근거 수집 전","1) Choose analysis input mode — before target evidence collection"))
        input_mode=st.radio(T("표적 근거를 어떻게 준비할까요?","How should target evidence be prepared?"),["자동 수집","원자료 입력"] if KO else ["Automatic collection","Upload source files"],horizontal=True,key="input_mode")
        auto_mode=input_mode in {"자동 수집","Automatic collection"}
        cfiles=[]; dfiles=[]; summary_file=None; confirm_human=False; auto_run=False; run=False
        # Files selected in the current run only; existing raw files are not
        # silently reused on a later rerun.
        active_raw_files=[]
        st.subheader(T("실시간 실행 콘솔","Live execution console"))
        console=st.empty()
        def update_console():
            log_path=p/"logs/analysis_log.txt"
            text=log_path.read_text(encoding="utf-8")[-6000:] if log_path.exists() else T("아직 실행 로그가 없습니다.","No execution log yet.")
            console.code(text,language="text")
        if auto_mode:
            auto_metadata_path=p/"01_np/raw/auto_api_retrieval_metadata.json"
            auto_files_ready=auto_metadata_path.exists() and any((p/"01_np/raw/compound_targets").glob("auto_pubchem_*_active_bioassay_targets.csv")) and (p/"01_np/raw/disease_targets/auto_opentargets_disease_targets.csv").exists()
            if auto_files_ready:
                st.success(T("자동수집 자료가 이미 저장되어 있습니다. 기존 자료를 다시 수집하지 않습니다.","Automatic collection is already complete and saved. Existing source files will not be collected again."))
            st.info(T("PubChem 활성 bioassay 표적과 Open Targets 질환-표적 근거를 자동으로 수집합니다. 별도 CSV 업로드나 species 체크는 필요 없습니다.","Active PubChem bioassay targets and Open Targets disease associations will be collected automatically. No CSV upload or species confirmation is needed."))
            pharmmapper_enable=st.checkbox(T("PharmMapper 보조 수집 사용","Use PharmMapper as a supplementary source"),key="pharmmapper_enable")
            if pharmmapper_enable:
                st.markdown(T("[PharmMapper 공식 사이트 열기](https://www.lilab-ecust.cn/pharmmapper/)","[Open the official PharmMapper site](https://www.lilab-ecust.cn/pharmmapper/)"))
                pharm_email=st.text_input(T("PharmMapper 제출용 이메일","Email for PharmMapper submission"),key="pharmmapper_email",placeholder="name@example.org")
                pharm_consent=st.checkbox(T("PharmMapper에 직접 제출하고 결과 메일을 확인했습니다.","I submitted directly to PharmMapper and checked the result email."),key="pharmmapper_consent")
                st.caption(T("앱은 PharmMapper에 자동 제출하거나 Gmail을 읽지 않습니다. 공식 결과 CSV를 받은 뒤 아래 업로드 칸에 추가하세요.","The app does not submit to PharmMapper or read Gmail. Upload the official result CSV after receiving it."))
                pharm_files=st.file_uploader(T("PharmMapper 결과 CSV (선택)","PharmMapper result CSV (optional)"),type="csv",accept_multiple_files=True,key="pharmmapper_files")
            auto_run=st.button(T("자동 수집 + ID/QC + overlap + STRING + enrichment 실행","Auto-collect + ID/QC + overlap + STRING + enrichment"),type="primary",disabled=auto_files_ready,help=T("PubChem의 활성 bioassay 표적과 Open Targets 질환-표적 연관을 자동 수집합니다. PubChem 표적은 MyGene에서 사람 유전자로 확인된 경우에만 분석에 포함됩니다.","Automatically retrieves active PubChem bioassay targets and Open Targets disease associations. PubChem targets enter analysis only after MyGene confirms a human gene mapping."))
        else:
            st.info(T("직접 확보한 CSV·TSV·ZIP을 추가하거나, 자동 수집 대신 원자료만 사용합니다. 화합물 표적과 질환 표적을 각각 하나 이상 업로드해야 합니다.","Use your own CSV, TSV, or ZIP source files instead of automatic collection. Upload at least one compound-target and one disease-target source."))
            contact_email=st.text_input(T("선택: 외부 작업 완료 알림 이메일","Optional: external-job notification email"),key="contact_email",placeholder="name@example.org",help=T("이 앱은 이메일을 자동 발송하거나 저장하지 않습니다. 외부 서비스 제출 화면 또는 승인된 Gmail 연동에서만 사용합니다.","This app does not send or persist email. Use it only on the provider submission page or with an explicitly approved Gmail connection."))
            email_consent=st.checkbox(T("이메일이 필요한 외부 서비스에 제출하기 전에 매번 확인하겠습니다.","I will confirm before submitting to an external service that requires email."),key="email_submission_consent")
            if contact_email and not email_consent:
                st.warning(T("이메일을 입력했지만 제출 승인이 아직 선택되지 않았습니다. 이 앱은 외부 서비스에 자동 제출하지 않습니다.","An email was entered, but submission consent is not checked. This app will not submit to external services automatically."))
            project_compounds=manifest.get("compounds") or [manifest.get("compound",{})]
            with st.expander(T("외부 표적예측 도구 안내: SwissTargetPrediction · SEA · PharmMapper","Guide: SwissTargetPrediction · SEA · PharmMapper"),expanded=True):
                st.markdown(T("공식 사이트: [SwissTargetPrediction](https://www.swisstargetprediction.ch/) · [SEA Search Server](https://sea.docking.org/) · [PharmMapper](https://www.lilab-ecust.cn/pharmmapper/)","Official sites: [SwissTargetPrediction](https://www.swisstargetprediction.ch/) · [SEA Search Server](https://sea.docking.org/) · [PharmMapper](https://www.lilab-ecust.cn/pharmmapper/)"))
                st.markdown(T("""
이 앱은 이들 웹사이트를 자동 조작하거나 이메일을 대신 제출하지 않습니다. 각 사이트에서 **직접** 결과를 내려받은 뒤, 원본 CSV·TSV·ZIP을 아래에 업로드하세요. ZIP/TSV 원본은 보존하고 분석용 CSV를 별도로 만듭니다.

1. **SwissTargetPrediction**: 아래 화합물의 isomeric SMILES를 사이트에 붙여넣고 organism을 **Homo sapiens**로 선택합니다. 결과 전체를 CSV로 내려받아 `probability`, `target`, `Uniprot ID` 등 원래 열을 유지하세요.
2. **SEA Search Server**: 동일한 구조를 제출하고 완료된 job 결과를 CSV로 내려받습니다. job URL, library/fingerprint, E-value 또는 score가 있으면 파일 열로 보존하세요. 실패·대기열도 분석 실패가 아니라 source 상태로 기록합니다.
3. **PharmMapper**: PubChem에서 해당 CID의 3D SDF를 내려받아 제출합니다. 사람 단백질 target set과 conformer 설정을 기록하고, 결과 CSV의 rank, fit score, UniProt ID를 유지하세요. 이메일을 요구하면 본인의 이메일을 해당 사이트에만 직접 입력하세요. 이메일은 이 앱에 입력하거나 업로드하지 마세요.
4. **업로드 전 확인**: 화합물별·source별 파일을 합치지 말고 각각 업로드하세요. 최소 표적 열 이름은 `target`, `gene`, `symbol`, `uniprot` 중 하나여야 합니다. `species`/`taxid`, `source`, `score`, `rank`, `job_url` 열을 유지하는 것을 권장합니다.
""","""
This app does not automate these websites or submit an email on your behalf. Download each source's original CSV, TSV, or ZIP yourself, then upload it below; the raw file is preserved and a separate analysis CSV is created.

1. **SwissTargetPrediction**: submit the isomeric SMILES below with **Homo sapiens**, and retain original target, probability, and UniProt columns.
2. **SEA Search Server**: submit the same structure, download the completed job CSV, and retain job URL, library/fingerprint, E-value, and score when supplied.
3. **PharmMapper**: download the PubChem 3D SDF for the CID, record the human target-set and conformer settings, and retain rank, fit score, and UniProt ID. If the site requires email, enter it only there; never enter it in this app or source CSV.
4. **Before upload**: keep one file per compound and source. A target column named `target`, `gene`, `symbol`, or `uniprot` is required; retain `species`/`taxid`, `source`, `score`, `rank`, and `job_url` where available.
"""))
                for compound in project_compounds:
                    st.markdown(f"#### {compound.get('name','—')} · PubChem CID {compound.get('pubchem_cid','—')}")
                    smiles=compound.get("isomeric_smiles") or compound.get("canonical_smiles") or T("SMILES가 없습니다. 프로젝트를 새로 만들 때 PubChem 구조를 다시 확정하세요.","No SMILES stored. Reconfirm the PubChem structure when creating a new project.")
                    st.code(smiles,language="text")
                    gpt_prompt=f"""나는 network pharmacology 연구를 수행 중이다. 아래 화합물에 대해 SwissTargetPrediction, SEA Search Server, PharmMapper의 공식 사이트를 이용해 표적 예측 원자료를 얻는 절차를 단계별로 안내해줘.

화합물명: {compound.get('name','')}
PubChem CID: {compound.get('pubchem_cid','')}
isomeric/canonical SMILES: {smiles}

필수 조건:
1. SwissTargetPrediction에서는 Homo sapiens를 선택한다.
2. SEA는 job URL, library/fingerprint, E-value 또는 score를 기록한다.
3. PharmMapper는 PubChem CID의 3D SDF를 사용하고, 사람 단백질 target set·conformer 설정·job ID를 기록한다.
4. 결과는 각 화합물·각 서비스별로 별도 CSV로 내려받는다. target/gene 또는 UniProt ID, species, source, score, rank, job URL 열은 삭제하지 않는다.
5. 서비스 약관과 로그인·CAPTCHA·이메일 요구를 우회하지 않는다. 이메일이 요구되면 나에게 직접 입력을 요청하고, 이메일을 결과 파일이나 분석 앱에 기록하지 않는다.
6. 결과를 해석하거나 임의 표적을 생성하지 말고, 공식 결과 CSV를 보존하는 단계까지만 안내한다."""
                    st.caption(T("아래 내용을 복사해 GPT에게 외부 서비스 작업을 안내받을 수 있습니다.","Copy the text below to ask GPT for guided use of the external services."))
                    st.code(gpt_prompt,language="text")
                disease=manifest.get("disease",{})
                gpt_context={"project":p.name,"compounds":[{"name":c.get("name"),"pubchem_cid":c.get("pubchem_cid"),"inchikey":c.get("inchikey"),"isomeric_smiles":c.get("isomeric_smiles"),"canonical_smiles":c.get("canonical_smiles")} for c in project_compounds],"disease":{"name":disease.get("name"),"ontology":disease.get("ontology"),"ontology_id":disease.get("ontology_id"),"iri":disease.get("iri")},"organism":{"name":"Homo sapiens","taxon_id":9606},"requested_sources":["SwissTargetPrediction","SEA Search Server","PharmMapper"],"required_return_files":"One original CSV per compound and source; do not merge source files.","required_columns":"Retain target/gene or UniProt ID, species/taxid, source, native score/rank, job URL/ID, and source-specific settings when available."}
                combined_prompt=f"""아래에 첨부한 `np_source_collection_context.json`을 읽고, 이 Network Pharmacology 프로젝트의 외부 표적 근거 수집을 도와줘.

목표: 첨부된 모든 화합물과 질환을 대상으로, 사람(Homo sapiens, taxid 9606) 기준의 표적 근거 원자료를 수집할 수 있도록 SwissTargetPrediction, SEA Search Server, PharmMapper의 공식 웹사이트 사용 절차를 진행하거나 단계별로 안내해줘.

필수 수행 원칙:
1. 화합물별·source별로 독립적으로 처리한다. 화합물이나 source의 결과를 임의로 합치지 않는다.
2. SwissTargetPrediction은 Homo sapiens를 선택하고, 원본 결과 CSV의 target, probability, UniProt ID를 보존한다.
3. SEA는 job URL/ID, library 또는 fingerprint, E-value/score를 보존한다.
4. PharmMapper는 PubChem CID의 정확한 3D SDF를 사용하며, 사람 단백질 target set, conformer 설정, job ID, rank/fit score/UniProt ID를 보존한다.
5. 각 다운로드 결과는 한 파일씩 그대로 보존한다. 결과가 없거나 실패·대기열·CAPTCHA·로그인이 발생하면 그것을 명시적으로 기록하고, 다른 source 결과로 대체하지 않는다.
6. 이메일, 비밀번호, API 키, CAPTCHA 또는 약관 동의가 필요하면 우회하거나 추측하지 말고 나에게 직접 요청한다. 개인 이메일은 결과 파일, 로그, 프롬프트 또는 이 앱에 기록하지 않는다.
7. 공식 사이트가 제공한 실제 결과만 사용한다. 표적·점수·순위를 추정하거나 생성하지 않는다.
8. 완료 후에는 채팅 표가 아니라 **다운로드 가능한 CSV 파일**로 결과를 제공한다. compound/source 조합마다 다음 두 파일을 별도로 제공한다.
   - `RAW_<compound>_<source>.csv`: 공식 사이트에서 내려받은 원본 파일을 수정하지 않고 보존한다.
   - `KIOM_UPLOAD_<compound>_<source>.csv`: 이 웹앱 업로드용 복사본이다. 실제 원본 값만 사용하고, 최소 `target`, `species`, `source` 열을 포함한다. 가능한 경우 `compound_name`, `pubchem_cid`, `uniprot_accession`, `native_score`, `native_score_name`, `rank`, `job_id`, `job_url`, `retrieved_date`, `evidence_class` 열도 포함한다. 원본의 score/rank 열은 삭제하지 않는다.
9. 마지막으로 `KIOM_source_collection_summary.csv`를 제공한다. 열은 `compound_name, pubchem_cid, source, status, raw_file, upload_file, records, job_id, job_url, notes`로 한다. 실패·대기·미지원 source도 한 행으로 남긴다.
10. 업로드용 CSV는 `target` 열에 사람이 읽을 수 있는 gene symbol 또는 stable ID를 넣고, 종이 확실하면 `species`에 `9606`을 넣는다. 종이 불명확하면 비워 두고 임의로 사람이라고 쓰지 않는다.
11. 내가 받을 파일은 `KIOM_UPLOAD_*.csv`와 `KIOM_source_collection_summary.csv`이다. 이 파일들을 KIOM NP 웹앱의 ‘화합물 표적 CSV’ 업로드 칸에 올리도록 안내한다. `RAW_*.csv`는 업로드하지 않아도 되지만 원본 근거로 보관한다.

이번 단계는 외부 source의 원자료 수집까지만이다. overlap, STRING, enrichment, docking 해석은 수행하지 않는다."""
                st.markdown("#### "+T("GPT에 한 번에 전달하기","One-shot handoff to GPT"))
                st.caption(T("아래 두 파일을 내려받아 GPT 대화에 함께 첨부한 뒤, 지시문을 복사해 보내세요.","Download both files, attach them in a GPT conversation, then copy and send the instruction."))
                st.download_button(T("GPT 작업 지시문 다운로드 (.md)","Download GPT instruction (.md)"),data=combined_prompt,file_name="np_gpt_source_collection_instruction.md",mime="text/markdown")
                st.download_button(T("화합물·질환 정보 다운로드 (.json)","Download compound/disease context (.json)"),data=json.dumps(gpt_context,ensure_ascii=False,indent=2),file_name="np_source_collection_context.json",mime="application/json")
                st.code(combined_prompt,language="text")
                st.caption(T("웹앱에 올릴 파일: `KIOM_UPLOAD_*.csv`와 `KIOM_source_collection_summary.csv`. 원본 `RAW_*.csv`는 별도 보관하세요.","Upload `KIOM_UPLOAD_*.csv` and `KIOM_source_collection_summary.csv` to the app; retain `RAW_*.csv` separately as source evidence."))
            # External-source queue: records human-approved submissions without attempting
            # to automate CAPTCHA, email confirmation, or provider terms.
            st.markdown("#### "+T("외부 source 작업 큐","External source job queue"))
            st.caption(T("각 화합물·source 작업을 독립적으로 기록합니다. 제출·대기·결과 도착 상태와 job URL을 저장할 수 있습니다.","Track each compound/source independently. Save submission status, job URL, and result arrival."))
            job_rows=[]
            source_options=["SwissTargetPrediction","SEA","PharmMapper"]
            status_options=["미제출","사용자 승인 대기","제출됨/처리 중","결과 도착","CSV 업로드 완료","실패/대기/미지원"] if KO else ["not_submitted","awaiting_user_approval","submitted/processing","result_available","csv_uploaded","failed/queued/unsupported"]
            existing_jobs=manifest.get("external_jobs",{})
            for ci,compound in enumerate(project_compounds):
                for source in source_options:
                    key=f"{compound.get('pubchem_cid','')}_{source}"
                    old=existing_jobs.get(key,{})
                    with st.expander(f"{compound.get('name','—')} · {source}",expanded=False):
                        st_status=st.selectbox(T("상태","Status"),status_options,index=status_options.index(old.get("status",status_options[0])) if old.get("status") in status_options else 0,key=f"job_status_{ci}_{source}")
                        st_job=st.text_input("job ID",value=old.get("job_id", ""),key=f"job_id_{ci}_{source}")
                        st_url=st.text_input("job URL",value=old.get("job_url", ""),key=f"job_url_{ci}_{source}")
                        job_rows.append((key,{"compound_name":compound.get("name"),"pubchem_cid":compound.get("pubchem_cid"),"source":source,"status":st_status,"job_id":st_job,"job_url":st_url,"updated_utc":now()}))
            if st.button(T("외부 작업 상태 저장","Save external job statuses"),key="save_external_jobs"):
                manifest["external_jobs"]={k:v for k,v in job_rows}
                manifest["analysis_updated_utc"]=now()
                save_json(p/"00_project/NP_manifest.json",manifest)
                st.success(T("외부 source 작업 상태를 manifest에 저장했습니다.","External source job statuses were saved to the manifest."))
            if "source_upload_nonce" not in st.session_state: st.session_state.source_upload_nonce=0
            if st.button(T("새 입력 목록으로 초기화","Reset source upload list"),key="reset_source_uploads"):
                for key in ["cfiles","dfiles","source_summary","pharmmapper_files",f"cfiles_{st.session_state.source_upload_nonce}",f"dfiles_{st.session_state.source_upload_nonce}",f"source_summary_{st.session_state.source_upload_nonce}"]:
                    st.session_state.pop(key,None)
                st.session_state.source_upload_nonce += 1
                st.rerun()
            upload_nonce=st.session_state.source_upload_nonce
            cfiles=st.file_uploader(T("화합물 표적 CSV/TSV/ZIP (PharmMapper / SwissTargetPrediction / SEA / PubChem / STITCH 등)","Compound-target CSV/TSV/ZIP exports"),type=["csv","tsv","tab","zip"],accept_multiple_files=True,key=f"cfiles_{upload_nonce}")
            summary_file=st.file_uploader(T("선택: GPT/외부수집 source 요약 CSV (분석에는 사용하지 않고 provenance로 보존)","Optional: GPT/external source summary CSV (preserved for provenance, not analyzed)"),type="csv",key=f"source_summary_{upload_nonce}")
            dfiles=st.file_uploader(T("질환 표적 CSV/TSV/ZIP (Open Targets / OMIM / TTD / GeneCards 등)","Disease-target CSV/TSV/ZIP exports"),type=["csv","tsv","tab","zip"],accept_multiple_files=True,key=f"dfiles_{upload_nonce}")
            upload_provenance={}
            upload_items=[("compound_targets",f) for f in (cfiles or [])]+[("disease_targets",f) for f in (dfiles or [])]
            if upload_items:
                st.markdown(T("#### 업로드 파일별 출처 확인","#### Source confirmation for each uploaded file"))
                st.caption(T("수집일·공식 결과 URL을 입력하고 확인을 체크하면 해당 파일은 VERIFIED로 기록됩니다. 이는 사용자가 확인한 출처라는 뜻이며, 앱이 다운로드 과정을 독립적으로 증명한다는 뜻은 아닙니다.","Enter the retrieval date and official result URL, then confirm. The file is recorded as VERIFIED by user attestation; the app does not independently prove the download."))
                for upload_index,(kind,uploaded_file) in enumerate(upload_items):
                    file_key=re.sub(r"[^a-zA-Z0-9]+","_",uploaded_file.name).strip("_")[:80] or str(upload_index)
                    st.markdown(f"**{uploaded_file.name}**")
                    url=st.text_input(T("공식 출처 URL 또는 job URL","Official source URL or job URL"),key=f"prov_url_{upload_nonce}_{kind}_{file_key}",placeholder="https://sea.docking.org/result?taskId=...")
                    retrieved_date=st.date_input(T("원자료 수집일","Original retrieval date"),value=None,key=f"prov_date_{upload_nonce}_{kind}_{file_key}")
                    confirmed=st.checkbox(T("이 파일의 URL과 수집일을 확인했습니다","I confirmed this file's URL and retrieval date"),key=f"prov_confirm_{upload_nonce}_{kind}_{file_key}")
                    date_text=retrieved_date.isoformat() if retrieved_date else ""
                    upload_provenance[(kind,uploaded_file.name)]=upload_provenance_status(url,date_text,confirmed)
            confirm_human=st.checkbox(T("업로드한 종 미기재 표적은 Homo sapiens (9606) 기준임을 확인했습니다","I confirm rows with missing species are human (9606)"),value=False)
            provenance_needs_review=bool(upload_items) and any(x.get("status")!="VERIFIED" for x in upload_provenance.values())
            # Provenance is recorded for every file, but incomplete provenance
            # is a labelled exploratory limitation rather than a second
            # blocking checkbox.
            allow_exploratory=True
            if provenance_needs_review:
                st.info(T("출처 URL·수집일이 없는 파일은 UNVERIFIED로 기록하고 broad exploratory 결과로 표시합니다. 분석 실행 자체는 막지 않습니다.","Files without a source URL or retrieval date are recorded as UNVERIFIED and labelled broad exploratory; analysis is not blocked."))
            elif upload_items:
                st.success(T("업로드 파일의 출처 URL·수집일·확인이 모두 입력되었습니다.","Source URL, retrieval date, and confirmation are complete for the uploaded files."))
            run=st.button(T("원자료 저장 + ID/QC + overlap + STRING + enrichment 실행","Save sources + ID/QC + overlap + STRING + enrichment"),type="primary")
        if auto_run and auto_files_ready:
            auto_run=False
        if auto_run:
            try:
                compounds=manifest.get("compounds") or [manifest.get("compound",{})]
                disease_query=manifest.get("disease",{}).get("name") or manifest.get("disease",{}).get("query")
                if not disease_query: raise ValueError("Automatic collection requires a confirmed disease name.")
                auto_compound=[]; compound_metadata=[]; no_pubchem_assay=[]
                for compound in compounds:
                    cid=compound.get("pubchem_cid")
                    if not cid: raise ValueError("Automatic collection requires a PubChem CID for every confirmed compound.")
                    rows=providers.pubchem_bioactivity_targets(cid)
                    item={"name":compound.get("name"),"cid":cid,"records":len(rows),"status":"active_targets_found" if rows else "no_public_assay_summary_or_active_gene_target"}
                    compound_metadata.append(item)
                    if not rows:
                        no_pubchem_assay.append(item)
                        continue
                    for row in rows: row["compound_name"]=compound.get("name","")
                    auto_path=p/f"01_np/raw/compound_targets/auto_pubchem_CID{cid}_active_bioassay_targets.csv"
                    write_csv(auto_path,rows)
                    active_raw_files.append(("compound_targets",auto_path))
                    auto_compound.extend(rows)
                auto_disease,ot_metadata=providers.opentargets_disease_targets(disease_query)
                auto_disease_path=p/"01_np/raw/disease_targets/auto_opentargets_disease_targets.csv"
                write_csv(auto_disease_path,auto_disease)
                active_raw_files.append(("disease_targets",auto_disease_path))
                save_json(p/"01_np/raw/auto_api_retrieval_metadata.json",{"retrieved_utc":now(),"compounds":{"provider":"PubChem PUG-REST","items":compound_metadata,"selection":"Activity Outcome = Active; NCBI Gene ID required; human status deferred to MyGene mapping"},"disease":{"provider":"Open Targets Platform GraphQL",**ot_metadata}})
                if not auto_compound:
                    auto_run=False
                    missing=", ".join(f"{x['name']} (CID {x['cid']})" for x in no_pubchem_assay)
                    log(p,f"AUTO_SOURCE_FALLBACK_REQUIRED | PubChem has no usable active-assay target export for: {missing} | next_sources=ChEMBL,BindingDB,SwissTargetPrediction,SEA,PharmMapper,STITCH")
                    update_console()
                    st.warning(T(f"PubChem 표적이 없는 화합물({missing})도 프로젝트에서 제외하지 않았습니다. ChEMBL·BindingDB 또는 공식 SwissTargetPrediction/SEA/PharmMapper/STITCH 결과를 source별로 추가하세요. 다른 화합물 표적은 복사하지 않습니다.",f"Compounds without PubChem targets ({missing}) remain in the project. Add ChEMBL/BindingDB or official source CSVs by source. Targets from another compound are never copied."))
                else:
                    log(p,f"AUTO_SOURCE_RETRIEVED | compounds={len(compound_metadata)} PubChem_records={len(auto_compound)} | OpenTargets={ot_metadata['disease_id']} records={len(auto_disease)}")
                    if no_pubchem_assay:
                        missing=", ".join(f"{x['name']} (CID {x['cid']})" for x in no_pubchem_assay)
                        st.warning(T(f"일부 화합물({missing})은 PubChem 표적이 없어 fallback source 입력을 기다립니다. 결과 해석 전 외부 source CSV를 보완하세요.",f"Some compounds ({missing}) have no PubChem targets and await fallback source input. Add external source CSVs before interpretation."))
                update_console()
                if auto_run:
                    st.info(T(f"자동 수집 완료: 화합물 {len(compound_metadata)}개에서 PubChem 활성 assay 표적 {len(auto_compound)}개, Open Targets 질환 표적 {len(auto_disease)}개. 이어서 QC와 네트워크 분석을 실행합니다.",f"Auto-collected {len(auto_compound)} active PubChem assay targets from {len(compound_metadata)} compounds and {len(auto_disease)} Open Targets disease targets. Continuing with QC and network analysis."))
            except Exception as e:
                auto_run=False; log(p,f"AUTO_SOURCE_FAILED | {type(e).__name__} | {e}"); update_console(); st.error(T(f"자동 수집 실패: {type(e).__name__}: {e}",f"Automatic collection failed: {type(e).__name__}: {e}"))
        if run or auto_run:
            try:
                # Preserve byte-identical source exports first.
                if summary_file:
                    (p/"01_np/raw"/"source_collection_summary.csv").write_bytes(summary_file.getvalue())
                uploaded_registry=[]
                for kind,files in [("compound_targets",cfiles or []),("disease_targets",dfiles or [])]:
                    for f in files:
                        payload=f.getvalue()
                        archive_dest=p/"00_project"/"source_archive"/Path(f.name).name
                        archive_dest.parent.mkdir(parents=True,exist_ok=True); archive_dest.write_bytes(payload)
                        if f.name.lower().endswith(".zip"):
                            # Earlier versions used the inner name directly and could
                            # leave sea_result*.csv behind after two ZIPs were uploaded.
                            # Move those recoverably into the archive before rebuilding
                            # collision-safe, ZIP-prefixed CSV names.
                            for legacy in (p/f"01_np/raw/{kind}/sea_result.csv", p/f"01_np/raw/{kind}/sea_result_all.csv"):
                                if legacy.exists():
                                    legacy_dest=p/"00_project"/"source_archive"/f"LEGACY_{legacy.name}_{now().replace(':','-')}.csv"
                                    shutil.move(str(legacy),str(legacy_dest))
                        try:
                            expanded_items=expand_source_upload(f.name,payload)
                        except Exception as error:
                            provenance=upload_provenance.get((kind,f.name),upload_provenance_status("","",False))
                            uploaded_registry.append({"entity":kind,"source":Path(f.name).stem,"raw_file":"","archive_file":str(archive_dest.relative_to(p)),"records":0,"provenance_status":provenance["status"],"verification_method":provenance["verification_method"],"source_url":provenance["source_url"],"retrieved_date":provenance["retrieved_date"],"retrieved_by":"user_upload","access_date":now(),"status":"INVALID_UPLOAD","notes":f"{type(error).__name__}: {error}"})
                            log(p,f"INVALID_UPLOAD | {kind}/{f.name} | {type(error).__name__}: {error} | skipped")
                            continue
                        for item in expanded_items:
                            base=normalized_upload_stem(f.name,item["name"])
                            dest=p/f"01_np/raw/{kind}/{base}.csv"
                            write_csv(dest,item["rows"])
                            active_raw_files.append((kind,dest))
                            provenance=upload_provenance.get((kind,f.name),upload_provenance_status("","",False))
                            uploaded_registry.append({"entity":kind,"source":base,"raw_file":str(dest.relative_to(p)),"archive_file":str(archive_dest.relative_to(p)),"records":len(item["rows"]),"provenance_status":provenance["status"],"verification_method":provenance["verification_method"],"source_url":provenance["source_url"],"retrieved_date":provenance["retrieved_date"],"retrieved_by":"user_upload","access_date":now()})
                if not any(kind=="compound_targets" for kind,_ in active_raw_files) or not any(kind=="disease_targets" for kind,_ in active_raw_files):
                    raise ValueError("At least one raw CSV in both compound-target and disease-target branches is required.")
                if not confirm_human and not auto_run: raise ValueError("Confirm the species for source rows before analysis; missing species must not be silently assumed human.")
                gate=source_panel_gate(uploaded_registry, any(kind=="compound_targets" for kind,_ in active_raw_files), any(kind=="disease_targets" for kind,_ in active_raw_files))
                if not gate["ready"] and not auto_run:
                    log(p,"SOURCE_REVIEW_PENDING | " + ", ".join(gate["reasons"]) + " | continuing as broad exploratory")
                    st.warning("출처 검토 전 broad exploratory 상태로 계속합니다: " + ", ".join(gate["reasons"]))
                checkpoint_path=p/"00_project/NP_checkpoint.json"
                stages=["LOAD_RAW_SOURCE_EXPORTS","SPECIES_AND_SCHEMA_QC","STABLE_ID_MAPPING","OVERLAP","STRING_PPI","ENRICHMENT","CYTOSCAPE_EXPORTS","MANIFEST_CHECKSUMS"]
                bar=st.progress(0); msg=st.empty()
                def stage(i,label):
                    bar.progress(i/len(stages),text=f"{i}/{len(stages)} · {label}"); msg.info(T("작업 중: ","Working: ")+label)
                    save_json(checkpoint_path,{"stage":label,"stage_number":i,"stage_total":len(stages),"status":"RUNNING","updated_utc":now()}); log(p,"RUNNING | "+label); update_console()
                comp=[]; dis=[]; registry=[]; mapping_error=None; api_notes=[]
                for kind,bucket in [("compound_targets",comp),("disease_targets",dis)]:
                    for active_kind,fp in sorted(active_raw_files,key=lambda item:(item[0],str(item[1]))):
                        if active_kind != kind: continue
                        stage(1,f"Importing {kind}/{fp.name}")
                        raw=read_csv(fp)
                        uploaded_meta=next((x for x in uploaded_registry if x["source"]==fp.stem),{})
                        if not raw:
                            registry.append({"entity":kind,"source":fp.stem,"raw_file":str(fp.relative_to(p)),"raw_sha256":file_sha(fp),"retrieved_by":uploaded_meta.get("retrieved_by","user_export"),"access_date":uploaded_meta.get("access_date",now()),"records":0,"primary_eligible":False,"status":"EMPTY_RESULT","provenance_status":uploaded_meta.get("provenance_status","UNVERIFIED")})
                            log(p,f"EMPTY_RESULT | {kind}/{fp.name} | skipped without aborting run")
                            continue
                        # SEA ZIPs also contain auxiliary similarity tables
                        # without a target/gene/symbol/UniProt column. Preserve
                        # those files as raw evidence but exclude them from the
                        # target QC, overlap, STRING and enrichment branches.
                        if not target_column_present(raw):
                            registry.append({"entity":kind,"source":fp.stem,"raw_file":str(fp.relative_to(p)),"raw_sha256":file_sha(fp),"retrieved_by":uploaded_meta.get("retrieved_by","user_export"),"access_date":uploaded_meta.get("access_date",now()),"records":len(raw),"primary_eligible":False,"status":"UNSUPPORTED_SCHEMA","provenance_status":uploaded_meta.get("provenance_status","UNVERIFIED"),"notes":"Auxiliary/non-target table preserved but skipped from target analysis"})
                            log(p,f"UNSUPPORTED_SCHEMA | {kind}/{fp.name} | preserved and skipped without aborting run")
                            continue
                        # Apply human assertion only to rows where species metadata is genuinely absent.
                        for row in raw:
                            if not any((row.get(k) or "").strip() for k in ["species","organism","taxid"]): row["species"]="9606"
                        validated=validate_target_rows(raw,fp.stem)
                        for x in validated: x["raw_file"]=str(fp.relative_to(p))
                        bucket.extend(validated)
                        registry.append({"entity":kind,"source":fp.stem,"raw_file":str(fp.relative_to(p)),"raw_sha256":file_sha(fp),"retrieved_by":uploaded_meta.get("retrieved_by","user_export"),"access_date":uploaded_meta.get("access_date",now()),"records":len(raw),"primary_eligible":False,"status":"IMPORTED_PENDING_ID_QC","provenance_status":uploaded_meta.get("provenance_status","UNVERIFIED")})
                stage(2,"Human species and schema QC")
                # Map gene symbols / UniProt / Entrez IDs via MyGene; ambiguous mappings remain unresolved.
                all_rows=comp+dis
                query_vals=sorted({r["target_submitted"] for r in all_rows if r["species_qc"] in {"PASS_HUMAN","PENDING_HUMAN_MAPPING"} and r["target_submitted"]})
                try:
                    map_response=providers.mygene_map(query_vals)
                except Exception as error:
                    mapping_error=f"{type(error).__name__}: {error}"
                    map_response=[]
                    log(p,f"MYGENE_MAPPING_FAILED | {mapping_error} | continuing with unmapped records")
                    st.warning(T(f"MyGene 매핑이 일시적으로 실패했습니다: {mapping_error}. 매핑되지 않은 표적은 제외하고 나머지 QC를 계속합니다.",f"MyGene mapping temporarily failed: {mapping_error}. QC continues with unmapped targets excluded."))
                api_notes.append({"provider":"MyGene.info","status":"FAILED_CONTINUED" if mapping_error else "COMPLETED","queries":len(query_vals),**({"error":mapping_error} if mapping_error else {})})
                map_index={}
                for mr in map_response:
                    q=(mr.get("query") or "").strip().upper(); symbol=(mr.get("symbol") or "").strip()
                    if not q: continue
                    map_index.setdefault(q,[]).append(mr)
                mapped=0
                for r in all_rows:
                    if r["species_qc"] not in {"PASS_HUMAN","PENDING_HUMAN_MAPPING"}: r["mapping_qc"]="EXCLUDED_SPECIES"; continue
                    hits=map_index.get(r["target_submitted"].upper(),[])
                    symbols=sorted({h.get("symbol") for h in hits if h.get("symbol") and h.get("taxid")==9606})
                    if len(symbols)==1:
                        chosen=next(h for h in hits if h.get("symbol")==symbols[0] and h.get("taxid")==9606)
                        uniprot=chosen.get("uniprot",{}).get("Swiss-Prot",[]) if isinstance(chosen.get("uniprot",{}),dict) else []
                        r["approved_symbol"]=symbols[0]; r["entrez_id"]=str(chosen.get("entrezgene", "")); r["uniprot_accessions"]=";".join(uniprot if isinstance(uniprot,list) else [str(uniprot)]); r["mapping_route"]="MyGene.info exact query; human taxid 9606"; r["mapping_qc"]="MAPPED_SINGLE_HUMAN_SYMBOL"; r["species_qc"]="PASS_HUMAN"; mapped+=1
                    elif len(symbols)>1: r["mapping_qc"]="AMBIGUOUS_ONE_TO_MANY"; r["species_qc"]="REVIEW_AMBIGUOUS_HUMAN_MAPPING" if r["species_qc"]=="PENDING_HUMAN_MAPPING" else r["species_qc"]
                    else: r["mapping_qc"]="UNMAPPED_OR_NOT_FOUND"; r["species_qc"]="EXCLUDE_NO_HUMAN_MAPPING" if r["species_qc"]=="PENDING_HUMAN_MAPPING" else r["species_qc"]
                stage(3,"Calculate source-traceable broad overlap")
                write_csv(p/"01_np/processed/compound_target_records_qc.csv",comp); write_csv(p/"01_np/processed/disease_target_records_qc.csv",dis)
                overlaps=overlap_rows(comp,dis); write_csv(p/"01_np/final/overlap_broad_exploratory_pending_review.csv",overlaps)
                # Primary branch only after human review; v1 deliberately leaves this as broad exploratory.
                stage(4,"STRING ID mapping and PPI retrieval")
                edges=[]; string_nodes=[]; string_ids=[]
                genes=[x["approved_symbol"] for x in overlaps if x.get("approved_symbol")]
                if genes:
                    try:
                        string_nodes=providers.string_map(genes)
                        string_ids=sorted({x.get("stringId") for x in string_nodes if x.get("stringId")})
                        edges=providers.string_network(string_ids,required_score=400) if string_ids else []
                        write_csv(p/"01_np/processed/string_mapping.tsv.csv",string_nodes)
                        write_csv(p/"01_np/final/string_edges_score400.tsv.csv",edges)
                        write_csv(p/"01_np/final/hub_topology_degree.csv",hub_metrics([{"approved_symbol":x} for x in genes],edges))
                        api_notes.append({"provider":"STRING","status":"COMPLETED" if edges else "NO_EDGES_RETURNED","mapped_ids":len(string_ids),"edges":len(edges),"score_threshold":400,"species":9606})
                    except Exception as e:
                        api_notes.append({"provider":"STRING","status":"FAILED","error":f"{type(e).__name__}: {e}"}); log(p,f"STRING_FAILED | {type(e).__name__} | {e}")
                stage(5,"STRING enrichment + g:Profiler GO/KEGG/Reactome")
                if string_ids:
                    try:
                        se=providers.string_enrichment(string_ids); write_csv(p/"01_np/final/string_enrichment.tsv.csv",se); api_notes.append({"provider":"STRING enrichment","status":"COMPLETED","terms":len(se)})
                    except Exception as e: api_notes.append({"provider":"STRING enrichment","status":"FAILED","error":str(e)})
                    try:
                        ge=providers.gprofiler_enrichment(genes); save_json(p/"01_np/final/gprofiler_enrichment.json",ge); api_notes.append({"provider":"g:Profiler","status":"COMPLETED","sources":["GO:BP","GO:CC","GO:MF","KEGG","REAC"]})
                    except Exception as e: api_notes.append({"provider":"g:Profiler","status":"FAILED","error":str(e)})
                stage(6,"Export Cytoscape node/edge tables and GraphML")
                write_cytoscape_exports(p,[{"approved_symbol":x,"string_id":next((m.get("stringId") for m in string_nodes if m.get("preferredName")==x),"")} for x in genes],edges)
                stage(7,"Update manifest, checksums and checkpoint")
                m=load_json(p/"00_project/NP_manifest.json",{})
                m["source_registry"]=registry;m["analysis_started_utc"]=m.get("analysis_started_utc",now());m["analysis_updated_utc"]=now();m["analysis_parameters"]={"species":9606,"string_required_score":400,"mapping_provider":"MyGene.info query API","overlap":"exact approved HGNC symbol after human mapping","branch":"broad_exploratory_pending_review","missing_species_assumed_human_after_user_confirmation":True};m["provider_runs"]=api_notes
                m["counts"]={"compound_rows":len(comp),"disease_rows":len(dis),"human_mapped_rows":mapped,"overlap_genes":len(overlaps),"string_nodes":len(string_ids),"string_edges":len(edges)}
                m["status"]="COMPLETED_WITH_REVIEW" if overlaps else "COMPLETED_NO_OVERLAP";m["transcriptomics"]={"status":"OPTIONAL_NOT_STARTED","branch":"02_transcriptomics"}
                m["files"]=[]
                for fp in sorted(p.rglob("*")):
                    if fp.is_file() and fp.name!="NP_manifest.json": m["files"].append({"path":str(fp.relative_to(p)),"sha256":file_sha(fp)})
                required_files=["01_np/processed/string_mapping.tsv.csv","01_np/final/string_edges_score400.tsv.csv","01_np/final/hub_topology_degree.csv","01_np/final/string_enrichment.tsv.csv","01_np/final/gprofiler_enrichment.json","03_cytoscape/nodes.csv","03_cytoscape/edges.csv","03_cytoscape/network.graphml"]
                findings=analysis_review_findings(m,required_files)
                m["review_findings"]=findings
                m["limitations"]=[x["message"] for x in findings if x.get("severity") in {"warning","error"}]
                cp={"stage":"NP_CORE_RUN","status":m["status"],"updated_utc":now(),"counts":m["counts"],"next_action":"Review ambiguous/unmapped records and source availability; do not call broad overlap primary before QC signoff."}
                save_json(checkpoint_path,cp)
                (p/"00_project/NP_checkpoint.md").write_text(f"# NP checkpoint\n\n- Status: {m['status']}\n- Human-mapped target records: {mapped}\n- Broad exploratory overlap: {len(overlaps)}\n- STRING mapped IDs / edges: {len(string_ids)} / {len(edges)}\n- Transcriptomics: OPTIONAL_NOT_STARTED\n- Mapping/QC signoff: PENDING\n- Source panel completeness: REVIEW REQUIRED\n",encoding="utf-8")
                log(p,f"RUN_COMPLETED | overlap={len(overlaps)} | mapped={mapped} | STRING_edges={len(edges)}")
                m["files"]=[]
                for fp in sorted(p.rglob("*")):
                    if fp.is_file() and fp.name!="NP_manifest.json": m["files"].append({"path":str(fp.relative_to(p)),"sha256":file_sha(fp)})
                save_json(p/"00_project/NP_manifest.json",m)
                bar.empty(); msg.empty(); update_console()
                final_message=T("분석 완료 — 공통 표적이 없습니다. 자동 수집 근거의 범위와 추가 자료원을 검토하세요." if not overlaps else "분석 완료 — overlap은 QC 검토 전 broad exploratory branch입니다. 아래 출처별 상태를 확인하세요.","Analysis complete — no common targets were found. Review evidence scope and add supplementary sources." if not overlaps else "Analysis complete — overlap is a broad exploratory branch pending QC; inspect provider statuses below.")
                st.success(final_message)
                for finding in findings:
                    if finding["severity"]=="error": st.error(finding["message"])
                    elif finding["severity"]=="warning": st.warning(finding["message"])
                    else: st.info(finding["message"])
                st.json({"counts":m["counts"],"provider_runs":api_notes})
                st.dataframe(overlaps,width="stretch")
                hub_path=p/"01_np/final/hub_topology_degree.csv"
                if hub_path.exists():
                    st.markdown("#### "+T("STRING degree 기반 hub 순위","STRING degree-based hub ranking"))
                    st.caption(T("네트워크 중심성은 직접 결합이나 작용을 증명하지 않습니다.","Network centrality does not prove direct binding or mechanism."))
                    st.dataframe(read_csv(hub_path).head(20) if hasattr(read_csv(hub_path),"head") else read_csv(hub_path)[:20],width="stretch")
            except Exception as e:
                log(p,f"RUN_FAILED | {type(e).__name__} | {e}")
                save_json(p/"00_project/NP_checkpoint.json",{"stage":"NP_CORE_RUN","status":"FAILED","updated_utc":now(),"error_type":type(e).__name__,"error":str(e),"next_action":"Fix the input or provider error and rerun from preserved raw files."})
                update_console(); st.error(f"{type(e).__name__}: {e}")
        st.divider()
        st.subheader(T("로컬 CLI / Cytoscape handoff","Local CLI / Cytoscape handoff"))
        st.code(f"Get-Content -LiteralPath '{(p/'logs/analysis_log.txt').resolve()}' -Wait -Tail 40",language="powershell")
        st.caption(T("Cytoscape에서 03_cytoscape/network.graphml을 열고 레이아웃·스타일을 편집하세요. 파일은 Cytoscape 결과가 아니라 입력 네트워크입니다.","Open 03_cytoscape/network.graphml in Cytoscape for styling. This is an input network, not a Cytoscape analysis result."))
        st.write(T("외부 분석기를 연결할 때는 setup/command/log/exit-code를 manifest에 기록하는 CLI adapter를 추가합니다. 임의 shell 명령을 앱에서 실행하지 않습니다.","CLI adapters will record executable, parameters, logs, and exit codes. The app does not run arbitrary shell commands."))

elif st.session_state.page=="프로젝트 관리":
    st.header(T("프로젝트 관리","Project management"))
    all_projects=sorted([p for p in root.glob("*") if p.is_dir() and (p/"00_project/NP_manifest.json").exists()],key=lambda p:p.stat().st_mtime,reverse=True) if root.exists() else []
    hidden_projects_path=root/"00_drafts/hidden_projects.json"
    hidden_projects=set(load_json(hidden_projects_path,[]) or [])
    if not all_projects:
        st.info(T("관리할 프로젝트가 없습니다.","There are no projects to manage."))
    else:
        st.dataframe([{"project":p.name,"last_modified":datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),"list_status":T("숨김","Hidden") if p.name in hidden_projects else T("표시","Visible")} for p in all_projects],hide_index=True,width="stretch")
        selected_name=st.selectbox(T("관리할 프로젝트 선택","Select a project to manage"),[p.name for p in all_projects],key="manage_project")
        selected=next(p for p in all_projects if p.name==selected_name)
        action_left,action_right=st.columns(2)
        if action_left.button(T("이 프로젝트 열기","Open this project"),key="manage_open"):
            set_project(selected); st.rerun()
        if selected.name in hidden_projects:
            if action_right.button(T("목록에 다시 표시","Show in list"),key="manage_unhide"):
                save_json(hidden_projects_path,sorted(hidden_projects-{selected.name})); st.rerun()
        else:
            if action_right.button(T("목록에서 숨기기","Hide from list"),key="manage_hide"):
                save_json(hidden_projects_path,sorted(hidden_projects|{selected.name})); st.rerun()
        st.divider()
        st.subheader(T("로컬 프로젝트 완전 삭제","Permanently delete local project"))
        st.error(T("이 기능은 선택한 프로젝트 폴더와 그 안의 원자료·결과·로그를 이 컴퓨터에서 완전히 삭제합니다. 휴지통으로 이동하지 않으며 되돌릴 수 없습니다.","This deletes the selected project folder, including raw data, results, and logs, from this computer. It does not move to Recycle Bin and cannot be undone."))
        confirmation=st.text_input(T(f"삭제하려면 정확히 다음 프로젝트 이름을 입력하세요: {selected.name}",f"To delete, type this exact project name: {selected.name}"),key="delete_project_confirmation")
        if st.button(T("이 프로젝트를 로컬에서 완전 삭제","Permanently delete this local project"),type="primary",disabled=confirmation!=selected.name,key="delete_project_button"):
            target=selected.resolve(); allowed_root=root.resolve()
            if target.parent!=allowed_root or not (target/"00_project/NP_manifest.json").exists():
                st.error(T("안전 검사 실패: 삭제 대상이 프로젝트 저장 폴더 바로 아래의 유효한 프로젝트가 아닙니다.","Safety check failed: target is not a valid project directly under the project storage folder."))
            else:
                shutil.rmtree(target)
                save_json(hidden_projects_path,sorted(hidden_projects-{selected.name}))
                if st.session_state.project and Path(st.session_state.project).resolve()==target: st.session_state.project=None
                st.session_state.page="분석 설정" if KO else "Analysis setup"
                st.rerun()

elif st.session_state.page=="Transcriptomics":
    st.header(T("선택형 인간 transcriptomics 후속 분석","Optional human transcriptomics follow-up"))
    st.info(T("기본 NP를 먼저 수행하고, 결과를 검토한 다음 같은 프로젝트에서 실행·건너뛰기·나중에 분석을 선택합니다.","Run and review core NP first; then choose run, skip, or defer within the same project."))
    if st.session_state.project and Path(st.session_state.project).exists():
        p=Path(st.session_state.project)
        choice=st.radio(T("Transcriptomics 상태","Transcriptomics status"),["나중에 분석","이번 분석 건너뛰기","검토된 DEG 결과 업로드","정규화 발현행렬에 limma 실행"] if KO else ["Analyze later","Skip this run","Upload reviewed DEG table","Run limma on normalized expression matrix"],key="transcriptomics_choice")
        gse=st.text_input("GEO accession (optional)",placeholder="GSE…")
        st.caption(T("GEO 데이터는 조직·세포, 질환군/대조군, 표본 수, 플랫폼을 검토한 후 사용하세요. limma 실행은 정규화된 log-scale 발현행렬을 입력으로 받습니다. raw count는 이 기능에 넣지 마세요.","Review GEO tissue/cell type, groups, sample size, and platform first. limma takes a normalized log-scale expression matrix; do not supply raw counts here."))
        tp=p/"02_transcriptomics"
        if "limma" in choice.lower():
            expr=st.file_uploader(T("발현행렬 CSV: gene 열 + sample ID별 열","Expression CSV: gene column + one column per sample"),type="csv",key="expr_matrix")
            meta=st.file_uploader(T("표본 메타데이터 CSV: sample_id, group 열","Sample metadata CSV: sample_id and group columns"),type="csv",key="sample_meta")
            st.caption(T("이 PC에 Rscript와 Bioconductor limma가 설치되어 있어야 합니다. 그룹은 정확히 2개여야 합니다.","This PC must have Rscript and Bioconductor limma installed. Exactly two groups are supported."))
            if st.button(T("로컬 R/limma 실행","Run local R/limma"),disabled=not(expr and meta)):
                run_dir=tp/"processed"/f"limma_{datetime.now().strftime('%Y%m%d_%H%M%S')}"; run_dir.mkdir(parents=True,exist_ok=True)
                expr_path=tp/"raw"/"expression_matrix.csv"; meta_path=tp/"raw"/"sample_metadata.csv"
                expr_path.write_bytes(expr.getvalue()); meta_path.write_bytes(meta.getvalue())
                script=Path(__file__).parent/"scripts/run_limma.R"
                try:
                    proc=subprocess.run(["Rscript",str(script),str(expr_path),str(meta_path),str(run_dir)],capture_output=True,text=True,timeout=3600)
                    (run_dir/"stdout.log").write_text(proc.stdout,encoding="utf-8"); (run_dir/"stderr.log").write_text(proc.stderr,encoding="utf-8")
                    status="COMPLETED" if proc.returncode==0 else "FAILED"
                    save_json(tp/"transcriptomics_status.json",{"status":status,"dataset_id":gse,"updated_utc":now(),"command":["Rscript",str(script),str(expr_path),str(meta_path),str(run_dir)],"return_code":proc.returncode,"separate_branch":"02_transcriptomics","interpretation":"DEG is disease-associated evidence, not causal target validation."})
                    log(p,f"TRANSCRIPTOMICS_LIMMA | {status} | exit={proc.returncode}")
                    if proc.returncode==0: st.success(T("limma 완료. 결과와 method record를 확인하세요.","limma completed. Review the results and method record.")); st.dataframe(__import__('pandas').read_csv(run_dir/"limma_DEG_results.csv"),width="stretch")
                    else: st.error(proc.stderr[-3000:] or proc.stdout[-3000:])
                except Exception as e:
                    log(p,f"TRANSCRIPTOMICS_LIMMA_FAILED | {type(e).__name__} | {e}"); st.error(f"{type(e).__name__}: {e}")
        else:
            f=st.file_uploader(T("검토 완료된 DEG CSV (gene, logFC, adjusted_p_value, dataset_id 권장)","Reviewed DEG CSV (gene, logFC, adjusted_p_value, dataset_id recommended)"),type="csv",key="deg_table")
            if st.button(T("Transcriptomics 상태 저장","Save transcriptomics decision")):
                status="DEFERRED" if "later" in choice.lower() or "나중" in choice else "SKIPPED" if "skip" in choice.lower() or "건너" in choice else "DEG_TABLE_UPLOADED"
                save_json(tp/"transcriptomics_status.json",{"status":status,"GEO_query_or_accession":gse,"updated_utc":now(),"interpretation":"Separate disease-evidence branch; DEG is not causal target validation."})
                if f and status=="DEG_TABLE_UPLOADED": (tp/"raw"/Path(f.name).name).write_bytes(f.getvalue())
                log(p,"TRANSCRIPTOMICS_STATUS | "+status); st.success(status)
    else: st.warning(T("먼저 프로젝트를 생성하거나 열어 주세요.","Create or open a project first."))

elif st.session_state.page=="범위 및 도움말":
    st.header(T("현재 구현·미연결 구분","Implemented vs. pending modules"))
    st.markdown("""
| Module | Current status |
|---|---|
| PubChem chemical identity / EBI OLS disease concept | Implemented API adapter |
| Automatic starting evidence | PubChem active bioassay targets + Open Targets disease associations; human mapping/QC remains mandatory |
| Source CSV preservation, species QC, MyGene mapping, overlap | Implemented; CSV is optional supplementary evidence; broad branch only, requires review |
| STRING mapping, network, enrichment | Implemented API adapters; verify live response/version in local environment |
| g:Profiler GO/KEGG/Reactome | Implemented API adapter; independent enrichment branch |
| Cytoscape | GraphML + node/edge exports; desktop styling is user-run |
| Predictor sites (SwissTargetPrediction / PharmMapper / SEA) | User-export import; automated scraping not implemented |
| OMIM / TTD / GeneCards disease retrieval | User-export import; Open Targets is connected automatically |
| Transcriptomics | Optional follow-up; local limma for reviewed normalized log-scale two-group matrices, or reviewed DEG import; raw-count DESeq2/GEO auto-selection not wired |
| Arbitrary local CLI invocation | Intentionally disabled; specific tested adapters required |
""")
    st.warning(T("기존 앱의 프로젝트 구조와 데이터 파일은 이 새 앱으로 자동 이전되지 않습니다. 전체 앱을 로컬에서 시험한 뒤 필요한 프로젝트 폴더를 직접 지정·복사해야 합니다.","Existing project folders are not automatically migrated. Test this app locally, then point to or copy existing project data deliberately."))
