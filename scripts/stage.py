#!/usr/bin/env python3
"""Stage every tracked public asset, keeping Pages Functions at repository root."""
import hashlib
import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
target = root / '.site'
if target.exists():
    raise SystemExit('.site already exists; use a fresh checkout for a complete deployment')
target.mkdir()
excluded = {'.gitignore', 'README.md'}
paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
assets = []
for name in filter(None, paths):
    if name in excluded or pathlib.PurePosixPath(name).parts[0] in {'.github', 'scripts', 'functions'}:
        continue
    source = root / name
    if source.is_symlink() or not source.is_file():
        raise SystemExit(f'Unsupported tracked asset: {name}')
    data = source.read_bytes()
    dest = target / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    assets.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
function = root / 'functions/[[path]].js'
if not function.is_file() or not (target / 'index.html').is_file():
    raise SystemExit('Missing homepage or existing catch-all Pages Function')
manifest = {
    '_source': 'Tracked repository files at ' + subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip(),
    'assets': assets,
    'function_sha256': hashlib.sha256(function.read_bytes()).hexdigest(),
}
(root / 'deployment-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Staged {len(assets)} public assets ({sum(x["path"].endswith(".html") for x in assets)} HTML pages); Pages Function preserved separately')
