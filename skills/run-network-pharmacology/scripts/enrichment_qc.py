#!/usr/bin/env python3
"""Validate enrichment result structure and generate an auditable QC summary."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def find_col(fieldnames, candidates):
    lowered = {x.lower(): x for x in fieldnames}
    for c in candidates:
        if c.lower() in lowered:
            return lowered[c.lower()]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input_csv')
    ap.add_argument('--output', required=True)
    ap.add_argument('--background', required=True, help='Recorded background/universe description')
    ap.add_argument('--correction', required=True, help='Multiple-testing method')
    ap.add_argument('--database-version', required=True)
    ap.add_argument('--tool', required=True)
    args = ap.parse_args()

    with open(args.input_csv, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames or []
    if not rows:
        raise SystemExit('Enrichment file is empty')

    term = find_col(fields, ['term','description','name','pathway'])
    p_adj = find_col(fields, ['adjusted_p_value','p.adjust','p_adj','fdr','padj'])
    members = find_col(fields, ['members','member_genes','genes','intersection'])
    count = find_col(fields, ['count','intersection_size'])
    ratio = find_col(fields, ['generatio','gene_ratio','GeneRatio'])
    ontology = find_col(fields, ['ontology','category','source','database'])

    issues = []
    for label, col in [('term',term),('adjusted_p',p_adj),('members',members)]:
        if not col:
            issues.append(f'missing_column:{label}')
    invalid_p = 0
    duplicate_terms = 0
    if p_adj:
        for r in rows:
            try:
                x = float(r[p_adj])
                if not 0 <= x <= 1:
                    invalid_p += 1
            except (ValueError, TypeError):
                invalid_p += 1
    if term:
        duplicate_terms = sum(v-1 for v in Counter(r[term].strip() for r in rows if r[term].strip()).values() if v > 1)

    report = {
        'tool': args.tool,
        'database_version': args.database_version,
        'background': args.background,
        'multiple_testing_correction': args.correction,
        'rows': len(rows),
        'detected_columns': {
            'term': term, 'adjusted_p': p_adj, 'members': members,
            'count': count, 'gene_ratio': ratio, 'ontology': ontology,
        },
        'invalid_adjusted_p_rows': invalid_p,
        'duplicate_term_rows': duplicate_terms,
        'issues': issues,
        'status': 'PASS' if not issues and invalid_p == 0 else 'REVIEW',
        'note': 'PASS confirms structural QC only; biological interpretation and redundancy review remain separate.'
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
