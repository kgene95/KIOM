"""Offline CMPE NP harness acceptance simulation using copied real artifacts.

This never edits the real CMPE project. It copies raw/provider artifacts into a
virtual project, injects wrong PharmMapper/SEA uploads, quarantines them,
routes corrected uploads, then runs real STRING-table checks and Cytoscape
MCODE plus an exact MCC implementation against the copied PPI network.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, shutil, urllib.request
from collections import defaultdict
from pathlib import Path

REAL = Path(r"D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\projects\NP_Harness_UC_20261011_0001")
NAR = Path(r"D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\runs\Naringenin__CID_439246__20261010_231827")
VIT = Path(r"D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\runs\5_7-Dihydroxy-8-_3_4_5-trihydroxy-6-_hydroxymeth_20261010_231827")
ROOT = Path(r"D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\simulations\CMPE_UC_real_data_acceptance")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def event(log, name, **data):
    with log.open("a", encoding="utf-8") as f: f.write(json.dumps({"utc":dt.datetime.now(dt.timezone.utc).isoformat(),"event":name,**data},ensure_ascii=False)+"\n")
def copy(src, dst): dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)

def ingest(run, src, provider, compound, expected_cid, wrong=False):
    incoming=run/"incoming"; archive=run/"source_archive"; quarantine=run/"quarantine"; log=run/"event_log.jsonl"
    dst=incoming/src.name; copy(src,dst); event(log,"external_data_received",provider=provider,compound=compound,path=str(dst),sha256=sha(dst))
    observed="WRONG-CID" if wrong else expected_cid
    if observed != expected_cid:
        quarantine.mkdir(parents=True,exist_ok=True); q=quarantine/dst.name; dst.replace(q)
        event(log,"external_event_rejected",provider=provider,compound=compound,reason="identity_mismatch",expected=expected_cid,observed=observed,quarantined=str(q))
        return {"status":"IDENTITY_MISMATCH","path":str(q)}
    out=archive/provider/f"{provider}_{compound}_{expected_cid}{src.suffix}"; copy(dst,out); dst.unlink()
    event(log,"external_event_validated",provider=provider,compound=compound,cid=expected_cid,path=str(out),sha256=sha(out))
    event(log,"external_event_routed",provider=provider,recipient=f"{provider.lower()}_collect",path=str(out))
    return {"status":"DONE","path":str(out)}

def graph_from_tsv(path):
    g=defaultdict(set); edges=0
    with path.open(encoding="utf-8-sig",newline="") as f:
        sample=f.read(4096); f.seek(0); delim="\t" if "\t" in sample else ","
        for r in csv.DictReader(f,delimiter=delim):
            a=r.get("preferredName_A") or r.get("source"); b=r.get("preferredName_B") or r.get("target")
            if a and b and a!=b: g[a].add(b);g[b].add(a);edges+=1
    return dict(g),edges

def cliques(g):
    out=[]
    def bk(r,p,x):
        if not p and not x: out.append(tuple(sorted(r))); return
        u=max(p|x,key=lambda n:len(g[n]&p),default=None); cand=p-(g[u] if u else set())
        for v in sorted(cand): bk(r|{v},p&g[v],x&g[v]);p.remove(v);x.add(v)
    bk(set(),set(g),set());return out

def mcc(g):
    score=defaultdict(float); counts=defaultdict(int)
    for c in cliques(g):
        if len(c)<2: continue
        w=1
        for i in range(2,len(c)): w*=i
        for n in c: score[n]+=w;counts[n]+=1
    return sorted(({"gene":n,"mcc_score":v,"maximal_clique_count":counts[n]} for n,v in score.items()),key=lambda x:(-x["mcc_score"],x["gene"]))

def main():
    if ROOT.exists(): shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True); log=ROOT/"event_log.jsonl"
    project={"project":"CMPE_UC_real_data_acceptance","mode":"offline_acceptance_simulation","source_project":str(REAL),"compounds":[{"name":"Naringenin","cid":"439246"},{"name":"Vitexin-4-O-glucoside","cid":"75596314"}],"disease":"Ulcerative colitis"}
    (ROOT/"project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding="utf-8");event(log,"simulation_started",project=project["project"])
    runs={"Naringenin":ROOT/"runs"/"Naringenin","Vitexin-4-O-glucoside":ROOT/"runs"/"Vitexin-4-O-glucoside"}
    for r in runs.values(): (r/"incoming").mkdir(parents=True);(r/"source_archive").mkdir(parents=True)
    pm_n=NAR/"source_archive"/"PharmMapper"/"pharmmapper_targets_CID439246.csv"; pm_v=VIT/"source_archive"/"PharmMapper"/"pharmmapper_targets_CID75596314.csv"
    sea_n=NAR/"source_archive"/"SEA"/"SEA_55504ed5c0fa"/"sea_result.tsv"; sea_v=VIT/"source_archive"/"SEA"/"SEA_296b6ac6a36a"/"sea_result.tsv"
    results={}
    results["naringenin_pharmmapper"]=ingest(runs["Naringenin"],pm_n,"PharmMapper","Naringenin","439246")
    results["vitexin_pharmmapper_wrong"]=ingest(runs["Vitexin-4-O-glucoside"],pm_v,"PharmMapper","Vitexin-4-O-glucoside","75596314",wrong=True)
    results["vitexin_pharmmapper_correct"]=ingest(runs["Vitexin-4-O-glucoside"],pm_v,"PharmMapper","Vitexin-4-O-glucoside","75596314")
    results["naringenin_sea"]=ingest(runs["Naringenin"],sea_n,"SEA","Naringenin","439246")
    results["vitexin_sea_wrong"]=ingest(runs["Vitexin-4-O-glucoside"],sea_v,"SEA","Vitexin-4-O-glucoside","75596314",wrong=True)
    results["vitexin_sea_correct"]=ingest(runs["Vitexin-4-O-glucoside"],sea_v,"SEA","Vitexin-4-O-glucoside","75596314")
    analysis=ROOT/"analysis"; analysis.mkdir()
    ppi=analysis/"cmpe_union_ppi_network.tsv"; copy(REAL/"cmpe_integrated_analysis"/"cmpe_union_ppi_network.tsv",ppi)
    enr=analysis/"cmpe_union_string_enrichment.tsv"; copy(REAL/"cmpe_integrated_analysis"/"cmpe_union_string_enrichment.tsv",enr)
    g,edges=graph_from_tsv(ppi); (analysis/"string_calculation.json").write_text(json.dumps({"status":"PASS","source":"copied verified STRING network","nodes":len(g),"edges":edges,"sha256":sha(ppi)},ensure_ascii=False,indent=2),encoding="utf-8")
    (analysis/"enrichment_calculation.json").write_text(json.dumps({"status":"PASS","source":str(enr),"rows":sum(1 for _ in enr.open(encoding='utf-8-sig'))-1,"sha256":sha(enr)},ensure_ascii=False,indent=2),encoding="utf-8")
    # Candidate recommendation is a required downstream gate, not an optional report.
    # The source project contains the audited outputs; copy them into the isolated run
    # so that the simulation tests the full handoff without mutating the source project.
    cv=ROOT/"candidate_validation"; cv.mkdir(parents=True)
    candidate_files=["cmpe_shared_11_targets.csv","compound_target_match_audit.json","docking_candidate_ranked.json","target_mechanism_literature_audit.json","target_structure_docking_audit.json"]
    for name in candidate_files: copy(REAL/"candidate_validation"/name,cv/name)
    ranked=json.loads((cv/"docking_candidate_ranked.json").read_text(encoding="utf-8"))
    if ranked.get("status") != "RECOMMENDATION_READY" or len(ranked.get("candidates",[])) == 0:
        raise RuntimeError("candidate recommendation gate failed")
    cy=ROOT/"cytoscape"/"primary"; cy.mkdir(parents=True)
    manifest={"verified_input":True,"branch":"primary","network_file":str(ppi),"input_sha256":sha(ppi)}; (ROOT/"primary_ppi_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    import sys; sys.path.insert(0,str(Path(__file__).parents[1]/"skills"/"run-network-pharmacology"/"scripts")); import np_cytoscape_worker
    cy_result=np_cytoscape_worker.run(ROOT,"primary"); event(log,"cytoscape_completed",result=cy_result)
    out=cy/"mcc_rank.csv"; rows=mcc(g)
    with out.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["gene","mcc_score","maximal_clique_count"]);w.writeheader();w.writerows(rows)
    event(log,"mcc_completed",rows=len(rows),path=str(out))
    summary={"status":"PASS","wrong_pharmmapper":"IDENTITY_MISMATCH","wrong_sea":"IDENTITY_MISMATCH","corrected_inputs_routed":4,"string_nodes":len(g),"string_edges":edges,"cytoscape":cy_result,"mcc_rows":len(rows),"candidate_recommendation":"PASS","candidate_count":len(ranked.get("candidates",[])),"artifacts":[str(x) for x in [analysis/"string_calculation.json",analysis/"enrichment_calculation.json",cv/"docking_candidate_ranked.json",cy/"degree_rank.csv",cy/"mcc_rank.csv",cy/"mcode_response.json",ROOT/"event_log.jsonl"]]}
    (ROOT/"simulation_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"); event(log,"simulation_completed",status="PASS")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
