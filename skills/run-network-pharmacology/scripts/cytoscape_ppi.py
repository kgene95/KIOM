#!/usr/bin/env python3
"""Create a reproducible Cytoscape PPI view from frozen CSV tables via py4cytoscape/cyREST."""
import argparse
import json
from pathlib import Path


def numeric_range(series):
    values = []
    for value in series:
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            pass
    if not values:
        return None
    lo, hi = min(values), max(values)
    if hi == lo:
        hi = lo + 1.0
    return [lo, hi]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--nodes', required=True)
    ap.add_argument('--edges', required=True)
    ap.add_argument('--node-id-col', default='gene')
    ap.add_argument('--source-col', default='source')
    ap.add_argument('--target-col', default='target')
    ap.add_argument('--interaction-col', default='interaction')
    ap.add_argument('--node-size-col', default='degree')
    ap.add_argument('--edge-width-col', default='score')
    ap.add_argument('--layout', default='force-directed')
    ap.add_argument('--network-name', default='PPI_frozen_branch')
    ap.add_argument('--style-name', default='NP_PPI_reproducible')
    ap.add_argument('--base-url', default='http://127.0.0.1:1234/v1')
    ap.add_argument('--svg', required=True)
    ap.add_argument('--record-json', required=True)
    args = ap.parse_args()

    try:
        import pandas as pd
        import py4cytoscape as p4c
    except ImportError as e:
        raise SystemExit('Cytoscape automation requires pandas and py4cytoscape; run environment_check.py first.') from e

    nodes = pd.read_csv(args.nodes)
    edges = pd.read_csv(args.edges)
    for col in [args.node_id_col]:
        if col not in nodes.columns:
            raise SystemExit(f'Node table missing required column: {col}')
    for col in [args.source_col, args.target_col]:
        if col not in edges.columns:
            raise SystemExit(f'Edge table missing required column: {col}')
    node_ids = set(nodes[args.node_id_col].astype(str))
    bad = edges[~edges[args.source_col].astype(str).isin(node_ids) | ~edges[args.target_col].astype(str).isin(node_ids)]
    if len(bad):
        raise SystemExit(f'{len(bad)} edge rows reference nodes absent from the frozen node table')

    # Cytoscape expects standard id/source/target names; copy without altering analytical values.
    cy_nodes = nodes.copy()
    cy_nodes['id'] = cy_nodes[args.node_id_col].astype(str)
    cy_edges = edges.copy()
    cy_edges['source'] = cy_edges[args.source_col].astype(str)
    cy_edges['target'] = cy_edges[args.target_col].astype(str)
    if args.interaction_col not in cy_edges.columns:
        cy_edges['interaction'] = 'interacts with'
    else:
        cy_edges['interaction'] = cy_edges[args.interaction_col].astype(str)

    version = p4c.cytoscape_version_info(base_url=args.base_url)
    suid = p4c.create_network_from_data_frames(
        nodes=cy_nodes,
        edges=cy_edges,
        title=args.network_name,
        collection='NP_Automation',
        base_url=args.base_url,
        node_id_list='id',
        source_id_list='source',
        target_id_list='target',
        interaction_type_list='interaction',
    )
    if isinstance(suid, dict):
        suid = suid.get('networkSUID') or suid.get('SUID') or suid

    defaults = {
        'NODE_SHAPE': 'ELLIPSE',
        'NODE_SIZE': 35,
        'EDGE_WIDTH': 1,
        'NETWORK_BACKGROUND_PAINT': '#FFFFFF',
    }
    label_map = p4c.map_visual_property('node label', 'id', 'p', network=suid, base_url=args.base_url)
    p4c.create_visual_style(args.style_name, defaults, [label_map], base_url=args.base_url)
    p4c.set_visual_style(args.style_name, network=suid, base_url=args.base_url)

    node_range = numeric_range(cy_nodes[args.node_size_col]) if args.node_size_col in cy_nodes.columns else None
    if node_range:
        p4c.set_node_size_mapping(
            args.node_size_col, table_column_values=node_range, sizes=[25, 70], mapping_type='c',
            style_name=args.style_name, network=suid, base_url=args.base_url
        )
    edge_range = numeric_range(cy_edges[args.edge_width_col]) if args.edge_width_col in cy_edges.columns else None
    if edge_range:
        p4c.set_edge_line_width_mapping(
            args.edge_width_col, table_column_values=edge_range, widths=[0.5, 4.0], mapping_type='c',
            style_name=args.style_name, network=suid, base_url=args.base_url
        )

    p4c.layout_network(args.layout, network=suid, base_url=args.base_url)
    p4c.fit_content(network=suid, base_url=args.base_url)
    svg_base = str(Path(args.svg).resolve().with_suffix(''))
    p4c.export_image(filename=svg_base, type='SVG', network=suid, base_url=args.base_url, overwrite_file=True)
    svg_path = svg_base + '.svg'

    record = {
        'cytoscape_version_info': version,
        'network_suid': suid,
        'network_name': args.network_name,
        'style_name': args.style_name,
        'layout': args.layout,
        'node_table': str(Path(args.nodes).resolve()),
        'edge_table': str(Path(args.edges).resolve()),
        'node_size_mapping': {'column': args.node_size_col, 'input_range': node_range, 'visual_range': [25, 70]},
        'edge_width_mapping': {'column': args.edge_width_col, 'input_range': edge_range, 'visual_range': [0.5, 4.0]},
        'svg': svg_path,
        'base_url': args.base_url,
        'note': 'Cytoscape alters visualization only; analytical values and frozen membership come from input tables.'
    }
    Path(args.record_json).write_text(json.dumps(record, indent=2, default=str) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2, default=str))


if __name__ == '__main__':
    main()
