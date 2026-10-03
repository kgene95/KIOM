#!/usr/bin/env python3
"""Same-frame heavy-atom RMSD. JSON atom labels or symmetry-aware RDKit SDF; no pose superposition."""
import argparse,json
from pathlib import Path

def json_rmsd(ref,pose):
    def load(path):
        rows=json.loads(Path(path).read_text())['atoms']; atoms={r['id']:r for r in rows if r['element'].upper() not in ('H','D')}
        if len(atoms)!=sum(r['element'].upper() not in ('H','D') for r in rows): raise ValueError('Duplicate heavy-atom IDs')
        return atoms
    x,y=load(ref),load(pose)
    if not x or x.keys()!=y.keys() or any(x[k]['element']!=y[k]['element'] for k in x): raise ValueError('Heavy-atom IDs/elements differ')
    n=len(x); return (sum(sum((float(a)-float(b))**2 for a,b in zip(x[k]['xyz'],y[k]['xyz'])) for k in x)/n)**0.5,n

def sdf_rmsd(ref,pose):
    try:
        from rdkit import Chem
        from rdkit.Chem import rdMolAlign
    except ImportError as e: raise RuntimeError('SDF mode requires RDKit') from e
    def load(path):
        m=next(iter(Chem.SDMolSupplier(str(path),removeHs=True)),None)
        if m is None or m.GetNumConformers()!=1: raise ValueError(f'Invalid single-conformer SDF: {path}')
        return m
    a,b=load(ref),load(pose)
    if a.GetNumHeavyAtoms()!=b.GetNumHeavyAtoms(): raise ValueError('Heavy-atom count differs')
    if not a.HasSubstructMatch(b,useChirality=True) or not b.HasSubstructMatch(a,useChirality=True): raise ValueError('Different connectivity or stereochemistry')
    return rdMolAlign.CalcRMS(a,b,maxMatches=100000),a.GetNumHeavyAtoms()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('native');p.add_argument('redocked');p.add_argument('--format',choices=['json','sdf'],required=True);p.add_argument('--output');a=p.parse_args()
    rmsd,n=(json_rmsd if a.format=='json' else sdf_rmsd)(a.native,a.redocked)
    result={'rmsd_angstrom':round(rmsd,6),'heavy_atoms':n,'coordinate_frame':'unaligned','mapping':'explicit IDs' if a.format=='json' else 'RDKit symmetry'}
    body=json.dumps(result,indent=2)
    if a.output:Path(a.output).write_text(body+'\n')
    print(body)
if __name__=='__main__':main()
