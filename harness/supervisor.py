"""Low-cost run supervisor.

Reconciles stalled/failed runs without model calls. Protected external/security
failures are escalated instead of retried; bounded local/transient failures are
requeued and recorded for the normal controller.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, time
from urllib.parse import urlparse
from pathlib import Path

PROTECTED = ("10013", "permission", "captcha", "approval", "login", "unauthorized", "forbidden")

def now(): return dt.datetime.now(dt.timezone.utc)
def read(p, default):
    try: return json.loads(p.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError): return default
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(tmp,p)
def event(run, payload):
    with (run/'event_log.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'at_utc':now().isoformat(),**payload},ensure_ascii=False)+'\n')
def artifact_fingerprint(run: Path):
    ignored={'event_log.jsonl','supervisor_state.json','supervisor_alert.json','harness_state.json','controller_heartbeat.json','work_queue.json'}
    latest=0.0; total=0; count=0
    for p in run.rglob('*'):
        if p.is_file() and p.name not in ignored:
            try:
                s=p.stat(); latest=max(latest,s.st_mtime); total+=s.st_size; count+=1
            except OSError:
                continue
    return {'latest_mtime':latest,'total_size':total,'file_count':count}
def blocker_report(run: Path, queue: dict):
    tasks={t.get('id'):t for t in queue.get('tasks',[])}; blockers=[]
    for task in queue.get('tasks',[]):
        status=str(task.get('status',''))
        if status == 'WAITING_EXTERNAL':
            blockers.append({'task_id':task.get('id'),'type':'external_artifact','reason':task.get('detail') or task.get('next_action') or '외부 결과 필요'})
        elif status == 'QUEUED':
            deps=[d for d in task.get('requires',[]) if str(tasks.get(d,{}).get('status')) != 'DONE']
            if deps:
                blockers.append({'task_id':task.get('id'),'type':'dependency','requires':deps})
            else:
                blockers.append({'task_id':task.get('id'),'type':'dispatch','reason':'선행 조건은 충족됐지만 dispatch되지 않음'})
    return blockers

def integrate_projects(workspace: Path):
    """Reconcile multi-constituent projects after child runs complete.

    A project-level extract (for example CMPE) is not another compound run.
    The supervisor therefore creates the paper-level integration only after
    all child runs have passed their own completion gates.
    """
    project_root = workspace.parent / 'projects'
    if not project_root.exists():
        return []
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from cmpe_project_integration import integrate
    except Exception as exc:
        return [{'project': 'project-integrator', 'status': 'FAILED', 'reason': repr(exc)}]
    outcomes = []
    for project_dir in sorted(project_root.iterdir()):
        project_file = project_dir / 'project.json'
        if not project_file.is_file():
            continue
        project = read(project_file, {})
        if len(project.get('run_ids', [])) < 2:
            continue
        if project.get('status') == 'PROJECT_INTEGRATED':
            manifest = project_dir / 'cmpe_project_manifest.json'
            try:
                baseline = manifest.stat().st_mtime
                child_latest = max((p.stat().st_mtime for run_id in project.get('run_ids', []) for p in (
                    workspace / 'runs' / run_id / 'request.json',
                    workspace / 'runs' / run_id / 'harness_state.json',
                    workspace / 'runs' / run_id / 'cytoscape' / 'primary' / 'degree_rank.csv') if p.is_file()), default=0.0)
                if child_latest <= baseline:
                    continue
            except OSError:
                pass
        try:
            manifest = integrate(project_dir)
            outcomes.append({'project': project.get('project_id', project_dir.name), 'status': manifest.get('status'), 'event': 'project_integrated'})
        except (RuntimeError, ValueError, FileNotFoundError) as exc:
            payload = {'project_id': project.get('project_id', project_dir.name), 'status': 'WAITING_CHILD_RUNS', 'reason': str(exc), 'updated_utc': now().isoformat()}
            write(project_dir / 'integration_status.json', payload)
            outcomes.append(payload)
    return outcomes
def inspect_run(run: Path, max_recoveries=2, stale_after_seconds=300):
    queue=read(run/'work_queue.json', {'tasks':[]}); state=read(run/'supervisor_state.json', {'recovery_count':0,'last_recovery_utc':None}); alerts=[]
    # Reconcile stale external gates written by an older worker version.  A
    # durable approval request must be visible as WAITING_USER immediately;
    # it must never masquerade as an unexplained WAITING_EXTERNAL stall.
    for task in queue.get('tasks', []):
        if task.get('status') != 'WAITING_EXTERNAL':
            continue
        result = read(run / 'worker_results' / f"{task.get('id')}.json", {}) or {}
        request = read(run / 'external_action_request.json', {}) or {}
        if result.get('status') == 'WAITING_USER' or request.get('status') == 'WAITING_USER':
            task['status'] = 'WAITING_USER'
            task['detail'] = result.get('reason') or request.get('reason') or '외부 작업 승인 필요'
            task['next_action'] = result.get('next_action') or '승인 조건 확인 후 재개'
            alerts.append({'task_id': task.get('id'), 'reason': task['detail'], 'action': task['next_action']})
    # Resume a previously gated task when the durable approval now covers its
    # requested provider.  This removes the need for a manual requeue after a
    # user has already granted the approval.
    approval = read(run / 'external_access_approval.json', {}) or {}
    approved_hosts = {urlparse(str(x)).netloc.lower() for x in approval.get('endpoints', []) if urlparse(str(x)).netloc}
    if approval.get('approved') is True:
        for task in queue.get('tasks', []):
            if task.get('status') != 'WAITING_USER':
                continue
            request = read(run / f"external_action_request_{task.get('id')}.json", {}) or read(run / 'external_action_request.json', {}) or {}
            requested_hosts = {urlparse(str(x)).netloc.lower() for x in request.get('endpoints', []) if urlparse(str(x)).netloc}
            if requested_hosts and requested_hosts.issubset(approved_hosts):
                task['status'] = 'READY_FOR_WORKER'
                task['next_attempt_at'] = now().isoformat()
                task['detail'] = '승인 범위 확인 후 supervisor 자동 재개'
                task['next_action'] = '승인된 외부 worker 실행'
                event(run, {'event': 'supervisor_approval_resume', 'task_id': task.get('id')})
    failed=[t for t in queue.get('tasks',[]) if t.get('status')=='FAILED']
    for task in failed:
        detail=str(task.get('detail') or task.get('info',{}).get('reason') or '').lower()
        if any(x in detail for x in PROTECTED):
            task['supervisor_status']='WAITING_APPROVAL_OR_ENVIRONMENT'; alerts.append({'task_id':task.get('id'),'reason':task.get('detail'),'action':'승인 또는 실행환경 보정 필요'})
            continue
        if int(state.get('recovery_count',0)) >= max_recoveries:
            alerts.append({'task_id':task.get('id'),'reason':'bounded supervisor recovery exhausted','action':'사용자 검토 필요'}); continue
        task['status']='READY_FOR_WORKER'; task['next_attempt_at']=now().isoformat(); task['detail']='supervisor auto-recovery: 재현 후 재수행'; task['supervisor_recovery']=int(task.get('supervisor_recovery',0))+1
        state['recovery_count']=int(state.get('recovery_count',0))+1; state['last_recovery_utc']=now().isoformat()
        event(run, {'event':'supervisor_requeued','task_id':task.get('id'),'recovery_count':state['recovery_count']})
    heartbeat=read(run/'controller_heartbeat.json',{}); updated=heartbeat.get('updated_utc')
    harness_state=read(run/'harness_state.json',{})
    progress_payload={
        'harness_status': harness_state.get('status'),
        'heartbeat_status': heartbeat.get('controller_status'),
        'heartbeat_error': heartbeat.get('last_error'),
        'task_statuses': [(t.get('id'), t.get('status'), t.get('updated_utc'), t.get('attempts')) for t in queue.get('tasks',[])],
        'artifacts': artifact_fingerprint(run),
    }
    progress_key=json.dumps(progress_payload, sort_keys=True, ensure_ascii=False)
    if progress_key != state.get('last_progress_key'):
        state['last_progress_key']=progress_key
        state['last_progress_utc']=now().isoformat()
        state.pop('no_progress_alerted_utc', None)
    active_statuses={'RUNNING','EXECUTING','DISPATCHED','WORKING'}
    active_worker=any(str(t.get('status','')).upper() in active_statuses for t in queue.get('tasks',[]))
    ready_count=sum(1 for t in queue.get('tasks',[]) if t.get('status') in {'READY_FOR_WORKER','RETRY_WAIT'})
    if ready_count and not active_worker:
        try:
            from np_controller import run_controller
            result=run_controller(run, max_cycles=1)
            event(run, {'event':'supervisor_dispatch_attempt','ready_count':ready_count,'result_status':result.get('status')})
            queue=read(run/'work_queue.json', queue)
        except Exception as exc:
            alerts.append({'task_id':'supervisor','reason':repr(exc),'action':'controller dispatch 재시도 필요'})
    blockers=blocker_report(run, queue)
    if not active_worker and state.get('last_progress_utc'):
        try:
            no_progress_age=(now()-dt.datetime.fromisoformat(state['last_progress_utc'])).total_seconds()
            if no_progress_age >= stale_after_seconds and not state.get('no_progress_alerted_utc'):
                alerts.append({'task_id':'supervisor','reason':f'worker progress absent for {int(no_progress_age)}s','action':'총괄 보고 및 재수행 가능한 task 재검토','blockers':blockers[:12]})
                state['no_progress_alerted_utc']=now().isoformat()
        except ValueError:
            pass
    if updated:
        try:
            age=(now()-dt.datetime.fromisoformat(updated)).total_seconds()
            if age>3600: alerts.append({'task_id':'controller','reason':f'heartbeat age {int(age)}s','action':'컨트롤러 재시작 필요'})
        except ValueError: pass
    # Alerts are a current view, not an append-only error history.  Clear a
    # resolved alert so the dashboard/heartbeat cannot keep reporting an old
    # failure after the task has completed or been recovered.
    write(run/'supervisor_alert.json',{'run_id':run.name,'updated_utc':now().isoformat(),'alerts':alerts})
    write(run/'supervisor_state.json',state); write(run/'work_queue.json',queue)
    event(run, {'event':'supervisor_cycle','recovered':state.get('recovery_count',0),'alerts':len(alerts)})
    return {'run':run.name,'recovered':state.get('recovery_count',0),'alerts':alerts}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workspace',required=True); ap.add_argument('--interval-seconds',type=int,default=60); ap.add_argument('--stale-after-seconds',type=int,default=300); ap.add_argument('--once',action='store_true'); args=ap.parse_args(); root=Path(args.workspace)/'runs'
    while True:
        for run in sorted(root.glob('*')) if root.exists() else []:
            if run.is_dir() and (run/'work_queue.json').exists(): print(json.dumps(inspect_run(run, stale_after_seconds=max(60,args.stale_after_seconds)),ensure_ascii=False), flush=True)
        for outcome in integrate_projects(Path(args.workspace)):
            print(json.dumps(outcome, ensure_ascii=False), flush=True)
        if args.once: break
        time.sleep(max(60,args.interval_seconds))
if __name__=='__main__': main()
