#!/usr/bin/env python3
"""Inspect local NP/Cytoscape execution capabilities without network side effects."""
import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.error import URLError

PACKAGES = {
    'pandas': ('pandas',),
    'networkx': ('networkx',),
    'py4cytoscape': ('py4cytoscape',),
    'gprofiler': ('gprofiler-official', 'gprofiler'),
    'requests': ('requests',),
}


def pkg_version(names):
    for name in names:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    return None


def command_info(candidates, version_args=('--version',)):
    cmd = next((c for c in candidates if shutil.which(c)), None)
    path = shutil.which(cmd) if cmd else None
    version = None
    if path:
        try:
            proc = subprocess.run([path, *version_args], capture_output=True, text=True, timeout=5)
            version = (proc.stdout or proc.stderr).strip().splitlines()[0][:200] if (proc.stdout or proc.stderr) else None
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {'command': cmd, 'path': path, 'version': version}


def cytoscape_status(host, port):
    url = f'http://{host}:{port}/v1/version'
    try:
        with urlopen(url, timeout=2) as r:
            body = r.read().decode('utf-8', errors='replace')
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {'raw': body[:500]}
        return {'reachable': True, 'url': url, 'response': payload}
    except (URLError, OSError, socket.timeout) as e:
        return {'reachable': False, 'url': url, 'error': str(e)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=1234)
    ap.add_argument('--output')
    args = ap.parse_args()

    packages = {}
    for module, dists in PACKAGES.items():
        present = importlib.util.find_spec(module) is not None
        packages[module] = {'present': present, 'version': pkg_version(dists) if present else None}

    binaries = {
        'python': command_info((os.path.basename(sys.executable), 'python', 'python3')),
        'Rscript': command_info(('Rscript',)),
        'cytoscape': command_info(('cytoscape', 'Cytoscape')),
    }

    report = {
        'captured_utc': datetime.now(timezone.utc).isoformat(),
        'runtime': {'python': sys.version.split()[0], 'platform': platform.platform()},
        'binaries': binaries,
        'python_packages': packages,
        'cyrest': cytoscape_status(args.host, args.port),
        'routing_hint': (
            'If cyREST is reachable, Cytoscape can be automated without GUI inspection. '
            'If unavailable, produce Cytoscape-ready tables and use code-based topology with explicit labeling.'
        ),
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
