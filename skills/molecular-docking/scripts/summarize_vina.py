#!/usr/bin/env python3
"""Extract every REMARK VINA RESULT pose from a Vina PDBQT to CSV."""
import argparse,csv,re
from pathlib import Path
PATTERN=re.compile(r'^REMARK VINA RESULT:\s*([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)')
def parse(path):
    rows=[];model=None;saw=False
    for line in Path(path).read_text().splitlines():
        if line.startswith('MODEL'):
            saw=True
            try:model=int(line.split()[1])
            except:raise ValueError('Invalid MODEL rank')
        m=PATTERN.match(line)
        if m:
            if saw and model is None:raise ValueError('RESULT outside MODEL')
            rows.append({'pose_rank':model if model is not None else len(rows)+1,'score_kcal_mol':float(m[1]),'rmsd_lb':float(m[2]),'rmsd_ub':float(m[3])})
        if line.startswith('ENDMDL'):model=None
    if not rows or len({r['pose_rank'] for r in rows})!=len(rows):raise ValueError('Missing results or duplicate pose ranks')
    return rows
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pdbqt');p.add_argument('--output',required=True);p.add_argument('--target',required=True);p.add_argument('--ligand',required=True);p.add_argument('--seed',required=True);p.add_argument('--config',required=True);p.add_argument('--protocol-id',default='');a=p.parse_args()
    rows=[dict(target=a.target,ligand=a.ligand,protocol_id=a.protocol_id,seed=a.seed,config=a.config,pose_file=a.pdbqt,**r) for r in parse(a.pdbqt)]
    with open(a.output,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(f'{len(rows)} poses; top-ranked score {rows[0]["score_kcal_mol"]:.3f} kcal/mol')
if __name__=='__main__':main()
