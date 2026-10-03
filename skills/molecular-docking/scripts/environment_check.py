#!/usr/bin/env python3
"""Inventory local docking capabilities and versions; no network calls or secrets."""
import argparse, importlib.metadata, importlib.util, json, platform, shutil, subprocess, sys
from datetime import datetime, timezone

PKGS={'rdkit':('rdkit',),'meeko':('meeko',),'openbabel':('openbabel','openbabel-wheel'),'Bio':('biopython',),'pandas':('pandas',),'prolif':('prolif',),'MDAnalysis':('MDAnalysis',)}
BINS={'vina':('vina',),'gnina':('gnina',),'obabel':('obabel',),'prepare_ligand':('mk_prepare_ligand.py','prepare_ligand'),'prepare_receptor':('mk_prepare_receptor.py','prepare_receptor'),'python':('python','python3')}

def ver(dists):
    for d in dists:
        try:return importlib.metadata.version(d)
        except importlib.metadata.PackageNotFoundError: pass
    return None

def cmdver(path):
    if not path:return None
    for flag in ('--version','-V','-v'):
        try:
            p=subprocess.run([path,flag],capture_output=True,text=True,timeout=5)
            s=(p.stdout or p.stderr).strip()
            if s:return s[:300]
        except Exception: pass
    return None

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output');a=p.parse_args()
    bins={}
    for k,cands in BINS.items():
        c=next((x for x in cands if shutil.which(x)),None); path=shutil.which(c) if c else None
        bins[k]={'command':c,'path':path,'version':cmdver(path)}
    pk={k:importlib.util.find_spec(k) is not None for k in PKGS}
    pv={k:ver(v) if pk[k] else None for k,v in PKGS.items()}
    for k in ('prepare_ligand','prepare_receptor'):
        if bins[k]['path'] and pv.get('meeko'): bins[k]['version']=pv['meeko']
    required={'vina':bool(bins['vina']['path']),'python':bool(bins['python']['path']),'receptor_prep':bool(bins['prepare_receptor']['path'] or bins['obabel']['path']),'ligand_prep':bool(bins['prepare_ligand']['path'] or bins['obabel']['path'])}
    report={'captured_utc':datetime.now(timezone.utc).isoformat(),'runtime':{'python':sys.version.split()[0],'platform':platform.platform()},'binaries':bins,'python_packages':pk,'package_versions':pv,'default_vina_path_ready':all(required.values()),'required_capabilities':required,'notes':['GUI visibility is not required for terminal execution.','RDKit is required for symmetry-aware SDF RMSD.','ProLIF is optional for structured interaction fingerprints.']}
    body=json.dumps(report,indent=2)
    if a.output: open(a.output,'w',encoding='utf-8').write(body+'\n')
    print(body)
if __name__=='__main__':main()
