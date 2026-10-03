#!/usr/bin/env python3
"""Summarize hub stability across prespecified network scenarios without creating new hub scores."""
import argparse
import csv
import statistics
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input_csv', help='Rows with scenario,gene,rank and optional metric/score')
    ap.add_argument('--output', required=True)
    ap.add_argument('--scenario-col', default='scenario')
    ap.add_argument('--gene-col', default='gene')
    ap.add_argument('--rank-col', default='rank')
    ap.add_argument('--metric-col', default='metric')
    args = ap.parse_args()

    with open(args.input_csv, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit('Input is empty')
    for c in (args.scenario_col, args.gene_col, args.rank_col):
        if c not in rows[0]:
            raise SystemExit(f'Missing required column: {c}')

    scenarios = sorted({r[args.scenario_col].strip() for r in rows if r[args.scenario_col].strip()})
    if len(scenarios) < 2:
        raise SystemExit('Robustness requires at least two prespecified scenarios')
    by_gene = defaultdict(list)
    for r in rows:
        gene = r[args.gene_col].strip()
        scen = r[args.scenario_col].strip()
        if not gene or not scen:
            continue
        try:
            rank = float(r[args.rank_col])
        except ValueError:
            raise SystemExit(f'Non-numeric rank for {gene} in {scen}')
        by_gene[gene].append((scen, rank, r.get(args.metric_col, '')))

    out = []
    total = len(scenarios)
    for gene, vals in sorted(by_gene.items()):
        present = sorted({v[0] for v in vals})
        ranks = [v[1] for v in vals]
        metrics = sorted({v[2] for v in vals if v[2]})
        out.append({
            'gene': gene,
            'scenarios_present': len(present),
            'scenarios_total': total,
            'presence_fraction': round(len(present)/total, 6),
            'median_rank': round(statistics.median(ranks), 6),
            'best_rank': min(ranks),
            'worst_rank': max(ranks),
            'rank_range': max(ranks)-min(ranks),
            'metrics': ';'.join(metrics),
            'scenario_list': ';'.join(present),
            'robustness_class': 'stable_all' if len(present) == total else ('stable_majority' if len(present)/total >= 0.5 else 'unstable'),
        })
    fieldnames = list(out[0]) if out else []
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(out)
    print(f'{len(out)} genes summarized across {total} scenarios')


if __name__ == '__main__':
    main()
