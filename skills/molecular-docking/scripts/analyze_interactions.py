#!/usr/bin/env python3
"""Check structured interaction-analysis capability. Optionally create a machine-readable NOT_RUN record when ProLIF prerequisites are unavailable."""
import argparse, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--require-prolif',action='store_true');a=p.parse_args()
    mods={m:importlib.util.find_spec(m) is not None for m in ('prolif','MDAnalysis','rdkit')}
    ready=all(mods.values())
    result={'captured_utc':datetime.now(timezone.utc).isoformat(),'prolif_stack':mods,'status':'READY' if ready else 'NOT_RUN','reason':None if ready else 'Missing one or more ProLIF/MDAnalysis/RDKit dependencies. Use a documented alternative or install the missing stack.'}
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    if a.require_prolif and not ready: raise SystemExit(2)
if __name__=='__main__':main()
