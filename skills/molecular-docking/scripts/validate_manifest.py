#!/usr/bin/env python3
"""Validate docking manifest state, provenance and artifact SHA256 hashes."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
STATUSES={'PENDING','PASS','BORDERLINE','FAIL','NATIVE_UNAVAILABLE','LIMITED','UNVALIDATED'}
def utc_datetime(value):
    if not isinstance(value,str) or not value.strip():raise ValueError('blank timestamp')
    parsed=datetime.fromisoformat(value.strip().replace('Z','+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset()!=timezone.utc.utcoffset(parsed):raise ValueError('timestamp must include UTC offset')
    return parsed
def validate_v2_metadata(d):
    errors=[];timestamps={}
    try:timestamps['analysis_started_utc']=utc_datetime(d.get('analysis_started_utc'))
    except:errors.append('schema v2 requires valid UTC analysis_started_utc')
    completed=d.get('analysis_completed_utc')
    if completed:
        try:timestamps['analysis_completed_utc']=utc_datetime(completed)
        except:errors.append('analysis_completed_utc must be valid UTC when present')
    elif d.get('status')=='CLOSED':errors.append('CLOSED schema v2 job requires analysis_completed_utc')
    if len(timestamps)==2 and timestamps['analysis_completed_utc']<timestamps['analysis_started_utc']:errors.append('analysis_completed_utc precedes analysis_started_utc')
    env=d.get('environment')
    if not isinstance(env,dict) or not all(env.get(k) for k in ('python','platform')):errors.append('schema v2 requires environment.python and environment.platform')
    rows=d.get('software_inventory')
    if not isinstance(rows,list) or not rows:errors.append('schema v2 requires nonempty software_inventory')
    else:
        for i,row in enumerate(rows):
            if not isinstance(row,dict) or any(not str(row.get(k) or '').strip() for k in ('name','version','role')):errors.append(f'software_inventory row {i}: missing name, version, role')
    db=d.get('database_inventory')
    if d.get('stage',0)>=2 or d.get('status')=='CLOSED':
        if not isinstance(db,list) or not db:errors.append('schema v2 stage 2+ requires nonempty database_inventory')
        else:
            for i,row in enumerate(db):
                if not isinstance(row,dict) or any(not str(row.get(k) or '').strip() for k in ('name','release_or_version','access_date')):errors.append(f'database_inventory row {i}: missing name, release_or_version, access_date')
    return errors
def validate(path):
    base=Path(path).resolve().parent;d=json.loads(Path(path).read_text());req={'schema_version','project','job_id','target','ligands','stage','completed_stages','validation_status','status','receptor','protocol','files','issues','next_action'}
    errors=[f'missing {k}' for k in sorted(req-d.keys())]
    if errors:return errors
    if d['schema_version'] not in {'1','2'}:errors.append('unsupported schema_version')
    if d['schema_version']=='2':errors.extend(validate_v2_metadata(d))
    done=d['completed_stages']
    if not isinstance(done,list) or any(type(x) is not int or not 0<=x<=10 for x in done) or done!=sorted(set(done)):errors.append('completed_stages must be unique ascending integers 0-10')
    if type(d['stage']) is not int or not 0<=d['stage']<=10:errors.append('stage must be 0-10')
    if d['validation_status'] not in STATUSES:errors.append('invalid validation_status')
    if d['status'] not in {'OPEN','BLOCKED','CLOSED'}:errors.append('invalid status')
    if not isinstance(d['ligands'],list) or not d['ligands']:errors.append('missing ligand identities')
    for k in ('pdb_id','chain','source_date'):
        if not isinstance(d['receptor'],dict) or not d['receptor'].get(k):errors.append(f'receptor: missing {k}')
    for k in ('id','engine','version','grid','seeds','config_path'):
        if not isinstance(d['protocol'],dict) or k not in d['protocol']:errors.append(f'protocol: missing {k}')
    if isinstance(d['files'],dict):
        for rel,digest in d['files'].items():
            f=(base/rel).resolve()
            try:inside=f.is_relative_to(base)
            except AttributeError:inside=str(f).startswith(str(base))
            if not inside:errors.append(f'path escapes job: {rel}');continue
            if not f.is_file():errors.append(f'file absent: {rel}');continue
            if hashlib.sha256(f.read_bytes()).hexdigest()!=digest:errors.append(f'hash mismatch: {rel}')
    else:errors.append('files must map relative paths to SHA256')
    if any(x>=6 for x in done):
        if d['validation_status'] not in {'PASS','LIMITED'}:errors.append('docking requires PASS or explicitly LIMITED alternate validation')
        if d['validation_status']=='LIMITED' and not d.get('alternate_validation_rationale'):errors.append('LIMITED requires alternate_validation_rationale')
    if d['validation_status']=='FAIL' and d['status']!='BLOCKED':errors.append('FAIL must be BLOCKED')
    if d['status']=='CLOSED' and not {5,6,7,8}.issubset(done):errors.append('CLOSED needs validation, docking, pose QC and interaction stages')
    return errors
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');a=p.parse_args();issues=validate(a.manifest);print('\n'.join(issues) if issues else 'Manifest valid; listed artifacts match SHA256');raise SystemExit(bool(issues))
if __name__=='__main__':main()
