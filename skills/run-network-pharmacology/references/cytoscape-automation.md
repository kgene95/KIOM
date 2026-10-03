# Cytoscape automation

Use Cytoscape only after a PPI branch and its node/edge tables are frozen. Cytoscape may change layout and visual encodings; it must not silently alter analytical membership, edges, weights, hub ranks, or branch identity.

## Capability routing

Run `scripts/environment_check.py`. If local cyREST is reachable, Cytoscape can be controlled through its REST interface even when the assistant cannot inspect or manipulate the GUI directly. If cyREST is unavailable, create Cytoscape-ready node/edge tables and use clearly named code-based graph metrics; do not label those outputs as Cytoscape, cytoHubba, or MCODE results.

## Reproducible execution

Prefer the official `py4cytoscape` package over hand-written REST calls when it is available. Use `scripts/cytoscape_ppi.py` for a minimal reproducible import/layout/style/export route; it communicates with Cytoscape through cyREST and requires `pandas` plus `py4cytoscape`. Supply frozen node and edge tables and record:

- Cytoscape/cyREST version when detectable;
- network/branch ID and source table hashes;
- node/edge key columns;
- layout name and any layout seed/parameters when available;
- exact node-size/color and edge-width mappings;
- style name;
- exported SVG/PDF/PNG path;
- automation record JSON.

A reference image may guide typography, spacing, label density, and layout choice only. It must never contribute nodes, edges, degree values, rankings, pathways, or statistics.

## Cytoscape apps

Use cytoHubba or MCODE only when those apps are actually installed and executed. Record app name/version, algorithm, parameters, and raw export. Otherwise compute named graph metrics or communities with a reproducible library and label them by the actual implementation.
