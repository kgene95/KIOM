#!/usr/bin/env python3
"""Execute AutoDock Vina with explicit receptor, ligand, config and seed; preserve command/log metadata."""
import argparse, json, pathlib, shutil, subprocess
from datetime import datetime, timezone

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receptor',required=True);p.add_argument('--ligand',required=True);p.add_argument('--config',required=True);p.add_argument('--seed',required=True,type=int);p.add_argument('--out',required=True);p.add_argument('--log',required=True);p.add_argument('--metadata',required=True);p.add_argument('--extra',nargs=argparse.REMAINDER,default=[]);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args(); exe=shutil.which('vina')
    if not exe: raise SystemExit('AutoDock Vina executable not found')
    cmd=[exe,'--receptor',a.receptor,'--ligand',a.ligand,'--config',a.config,'--seed',str(a.seed),'--out',a.out]+a.extra
    meta={'started_utc':datetime.now(timezone.utc).isoformat(),'executable':exe,'command':cmd,'receptor':a.receptor,'ligand':a.ligand,'config':a.config,'seed':a.seed,'out':a.out,'log':a.log,'dry_run':a.dry_run}
    if a.dry_run: rc=0; stdout='';stderr=''
    else:
        r=subprocess.run(cmd,capture_output=True,text=True);rc=r.returncode;stdout=r.stdout;stderr=r.stderr
        pathlib.Path(a.log).write_text((stdout or '')+('\nSTDERR\n'+stderr if stderr else ''),encoding='utf-8')
    meta.update(completed_utc=datetime.now(timezone.utc).isoformat(),returncode=rc,stdout_tail=stdout[-4000:],stderr_tail=stderr[-4000:])
    pathlib.Path(a.metadata).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(' '.join(cmd))
    if rc: raise SystemExit(rc)
if __name__=='__main__':main()
