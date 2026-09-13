"""Publish cached visual meshes and serve a local Three.js review page."""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit

from .review import find_blender

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT/'out/viewer'


def _write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value))
    temporary.replace(path)


def publish(build, destination=DATA):
    build, destination = Path(build).resolve(), Path(destination).resolve()
    if not json.loads((build/'saved-provenance.json').read_text())['passes']:
        raise ValueError('Saved visual provenance must pass before browser review')
    job = json.loads((build/'assembly-job.json').read_text())
    exporter = Path(__file__).with_name('viewer_export.py')
    exporter_hash = hashlib.sha256(exporter.read_bytes()).hexdigest()
    assets, missing = {}, []
    (destination/'assets').mkdir(parents=True, exist_ok=True)
    for ref, asset in job['assets'].items():
        directory = Path(asset['directory'])
        record = json.loads((directory/'asset.json').read_text())
        blend = directory/'part.blend'
        if hashlib.sha256(blend.read_bytes()).hexdigest() != record['blend_sha256']:
            raise ValueError('Corrupt visual cache: '+ref)
        key = hashlib.sha256((record['blend_sha256']+exporter_hash).encode()).hexdigest()
        target = destination/'assets'/f'{key}.bin'
        assets[ref] = dict(url=f'/data/assets/{key}.bin', definition_sha256=record['definition_sha256'])
        if not target.exists():
            missing.append(dict(reference=ref, blend=str(blend), collection=record['visual_collection'], target=str(target)))
    if missing:
        task = build/'viewer-job.json'
        task.write_text(json.dumps(dict(missing=missing)))
        with (build/'viewer-export.log').open('w') as log:
            subprocess.run([str(find_blender()), '--background', '--factory-startup', '--python-exit-code', '1',
                            '--python', str(exporter), '--', str(task)], stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=180)
    for asset in assets.values():
        payload = (destination/'assets'/Path(asset['url']).name).read_bytes()
        if not payload or len(payload) % 72:
            raise ValueError('Invalid browser triangle buffer')
        asset['sha256'] = hashlib.sha256(payload).hexdigest()
    manifest = dict(assembly=job['assembly'], assets=assets, seed=job['seed'], build=build.name,
                    visual_only=True)
    manifest['revision'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    manifest['updated'] = datetime.now(timezone.utc).isoformat()
    # Stable review slots let layouts update independently without discarding
    # the other saved reviews. Geometry buffers remain shared across layouts.
    assembly_id = job['assembly']['assembly_id']
    review_key = hashlib.sha256(assembly_id.encode()).hexdigest()
    reviews = destination/'reviews'
    reviews.mkdir(exist_ok=True)
    _write_json(reviews/f'{review_key}.json', manifest)
    index_path = destination/'reviews.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else dict(reviews=[])
    label = job['assembly'].get('label', assembly_id.removeprefix('aurelian-').replace('-', ' ').capitalize())
    entry = dict(id=assembly_id, label=label,
                 url=f'/data/reviews/{review_key}.json', revision=manifest['revision'])
    index['reviews'] = [r for r in index['reviews'] if r['id'] != assembly_id]+[entry]
    _write_json(index_path, index)
    _write_json(destination/'latest.json', manifest)
    return dict(url='http://127.0.0.1:8765', exported_parts=len(missing), reused_parts=len(assets)-len(missing))


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = unquote(urlsplit(path).path)
        if path.startswith('/data/'):
            root, relative = DATA, path[6:]
        elif path.startswith('/vendor/'):
            root, relative = ROOT/'viewer/node_modules/three', path[8:]
        else:
            root, relative = ROOT/'viewer', path.lstrip('/') or 'index.html'
        target = (root/relative).resolve()
        if not target.is_relative_to(root.resolve()) or target.is_dir():
            return str(ROOT/'out/nonexistent-viewer-path')
        return str(target)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('publish').add_argument('build', type=Path)
    commands.add_parser('serve').add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if args.command == 'publish':
        print(json.dumps(publish(args.build), indent=2))
    else:
        print(f'Elf review: http://127.0.0.1:{args.port}', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
