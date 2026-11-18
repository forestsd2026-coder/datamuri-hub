#!/usr/bin/env python3
"""Verify complete deployed assets and production host redirects without writes."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
base = sys.argv[1].rstrip('/')
if not base.startswith('https://') or not urllib.parse.urlparse(base).hostname.endswith('.datamuri-hub.pages.dev'):
    raise SystemExit('Pass the unique HTTPS Cloudflare Pages deployment URL')
manifest = json.loads((root / 'deployment-manifest.json').read_text())
headers = {'User-Agent': 'DatamuriDeploymentVerifier/1.0 (+https://github.com/forestsd2026-coder/datamuri-hub)'}

def verify_asset(asset):
    url = base + '/' + urllib.parse.quote(asset['path'])
    last_error = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
                data = response.read()
                result = {'path': asset['path'], 'status': response.status, 'sha256': hashlib.sha256(data).hexdigest()}
            if result['status'] == 200 and result['sha256'] == asset['sha256']:
                return {**result, 'matches_source': True}
            last_error = f'Content mismatch: {result}'
        except Exception as exc:
            last_error = str(exc)
        if attempt < 3:
            time.sleep(5)
    return {'path': asset['path'], 'matches_source': False, 'error': last_error}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
redirects = []
for host in ('datamuri-hub.pages.dev', 'datamuri.us.com'):
    url = f'https://{host}/blog/data-analytics-trends-2026?deployment-check=1'
    try:
        response = opener.open(urllib.request.Request(url, headers=headers), timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    expected = 'https://www.datamuri.us.com/blog/data-analytics-trends-2026?deployment-check=1'
    redirects.append({'host': host, 'status': response.code, 'location': response.headers.get('Location'),
                      'passed': response.code == 301 and response.headers.get('Location') == expected})

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    assets = list(pool.map(verify_asset, manifest['assets']))
with urllib.request.urlopen(urllib.request.Request('https://www.datamuri.us.com/', headers=headers), timeout=30) as response:
    production = {'url': response.url, 'status': response.status, 'homepage_present': b'Datamuri' in response.read()}
passed = all(a['matches_source'] for a in assets) and all(r['passed'] for r in redirects) and production['status'] == 200 and production['homepage_present']
receipt = {'_source': 'Live public HTTPS reads ' + datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'deployment_url': base, 'source': manifest['_source'], 'assets': assets,
           'redirects': redirects, 'production': production, 'passed': passed}
(root / 'deployment-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(f'{sum(a["matches_source"] for a in assets)}/{len(assets)} assets match source; redirects {sum(r["passed"] for r in redirects)}/2; production {production["status"]}')
if not passed:
    print(json.dumps(receipt, indent=2))
    raise SystemExit(1)
