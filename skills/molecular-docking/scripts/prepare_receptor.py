#!/usr/bin/env python3
"""Run Meeko receptor preparation and save command metadata. Advanced residue/water/cofactor decisions must be locked prospectively."""
import argparse, json, pathlib, shutil, subprocess
from datetime import datetime, timezone

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input');p.add_argument('output');p.add_argument('--metadata',required=True);p.add_argument('--extra',nargs=argparse.REMAINDER,default=[]);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args(); exe=shutil.which('mk_prepare_receptor.py') or shutil.which('prepare_receptor')
    if not exe: raise SystemExit('Meeko receptor preparation command not found')
    cmd=[exe,'-i',a.input,'-o',a.output]+a.extra
    meta={'captured_utc':datetime.now(timezone.utc).isoformat(),'tool':'Meeko receptor preparation','executable':exe,'command':cmd,'input':a.input,'output':a.output,'dry_run':a.dry_run}
    if a.dry_run: rc=0; out=''; err=''
    else:
        r=subprocess.run(cmd,capture_output=True,text=True);rc=r.returncode;out=r.stdout;err=r.stderr
        if rc: meta.update(returncode=rc,stdout=out[-4000:],stderr=err[-4000:]);pathlib.Path(a.metadata).write_text(json.dumps(meta,indent=2)+'\n');raise SystemExit(rc)
    meta.update(returncode=rc,stdout=out[-4000:],stderr=err[-4000:]);pathlib.Path(a.metadata).write_text(json.dumps(meta,indent=2)+'\n')
    print(' '.join(cmd))
if __name__=='__main__':main()
