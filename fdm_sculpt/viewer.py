"""Publish cached visual meshes and serve a local Three.js review page."""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit, parse_qs
import secrets

from .review import find_blender
from . import piece_ids

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT/'out/viewer'
API_TOKEN = secrets.token_urlsafe(32)


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
        if not target.exists() or not target.with_suffix('.json').exists():
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
        pieces = json.loads((destination/'assets'/Path(asset['url']).name).with_suffix('.json').read_text())['pieces']
        offset = 0
        for piece in pieces:
            if (not isinstance(piece.get('role'),str) or not piece['role'] or
                    type(piece.get('first_triangle')) is not int or piece['first_triangle'] != offset or
                    type(piece.get('triangle_count')) is not int or piece['triangle_count'] <= 0):
                raise ValueError('Invalid browser piece ranges')
            offset += piece['triangle_count']
        if offset != len(payload)//72:
            raise ValueError('Browser piece ranges do not cover geometry')
        asset['pieces'] = pieces
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


def attach_stl(build, destination=DATA):
    """Publish the exact STL represented by an exported manufacturing review."""
    build, destination = Path(build), Path(destination)
    manifest = json.loads((build/'viewer-review.json').read_text())
    payload = (build/'elf-spearman-proof.stl').read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != manifest.get('source_stl_sha256'):
        raise ValueError('STL does not match the displayed manufacturing review')
    downloads = destination/'downloads'
    downloads.mkdir(parents=True, exist_ok=True)
    (downloads/f'{digest}.stl').write_bytes(payload)
    manifest['stl_download'] = dict(
        url=f'/data/downloads/{digest}.stl', filename=f'{build.name}.stl',
        sha256=digest, bytes=len(payload),
        status='Trial STL — not digitally validated. Sliced support and detail checks failed; no physical trial yet.')
    manifest.pop('revision', None)
    manifest.pop('updated', None)
    manifest['revision'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    manifest['updated'] = datetime.now(timezone.utc).isoformat()
    assembly_id = manifest['assembly']['assembly_id']
    key = hashlib.sha256(assembly_id.encode()).hexdigest()
    index = json.loads((destination/'reviews.json').read_text())
    entry = next(r for r in index['reviews'] if r['id'] == assembly_id)
    entry['revision'] = manifest['revision']
    _write_json(destination/'reviews'/f'{key}.json', manifest)
    _write_json(destination/'reviews.json', index)
    _write_json(destination/'latest.json', manifest)
    _write_json(build/'viewer-review.json', manifest)
    return dict(revision=manifest['revision'], stl_download=manifest['stl_download'])


class Handler(SimpleHTTPRequestHandler):
    def json_response(self, value, status=200):
        if status == 200 and isinstance(value, dict):
            if 'assembly' in value and 'assets' in value:
                value = piece_ids.annotate(value, DATA)
            elif isinstance(value.get('review'), dict):
                value = dict(value, review=piece_ids.annotate(value['review'], DATA))
        payload = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def local_request(self):
        host = self.headers.get('Host', '')
        allowed = (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')
        return host in allowed and self.headers.get('Origin', 'http://'+host) == 'http://'+host

    def do_GET(self):
        if not self.local_request():
            self.send_error(403)
            return
        path = urlsplit(self.path)
        if path.path == '/data/latest.json' or (path.path.startswith('/data/reviews/') and path.path.endswith('.json')):
            try:
                return self.json_response(json.loads(Path(self.translate_path(self.path)).read_text()))
            except (ValueError, KeyError, OSError) as exc:
                return self.json_response(dict(error=str(exc)), 400)
        if not path.path.startswith('/api/'):
            return super().do_GET()
        from . import workshop
        try:
            if path.path == '/api/catalog':
                result = dict(models=workshop.public_models(), token=API_TOKEN)
            elif path.path == '/api/model':
                result = workshop.model_review(parse_qs(path.query).get('id',[''])[0])
            elif path.path == '/api/jobs':
                result = workshop.jobs()
            elif path.path == '/api/piece':
                result = piece_ids.lookup(parse_qs(path.query).get('id',[''])[0], DATA)
            elif path.path.startswith('/api/jobs/'):
                result = workshop.job_status(path.path.removeprefix('/api/jobs/'))
            else:
                return self.json_response(dict(error='Unknown endpoint'),404)
            self.json_response(result)
        except (ValueError,KeyError,OSError) as exc:
            self.json_response(dict(error=str(exc)),400)

    def do_POST(self):
        if not self.local_request() or self.headers.get('X-Workshop-Token') != API_TOKEN:
            return self.json_response(dict(error='Reload the local viewer to reconnect'),403)
        from . import workshop
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 65536:
                raise ValueError('Invalid request size')
            request = json.loads(self.rfile.read(length))
            if not isinstance(request,dict):
                raise ValueError('Expected an object')
            route = urlsplit(self.path).path
            if route == '/api/rows/plan':
                pinned = workshop.plan(request)
                result = dict(plan=pinned,review=workshop.manifest(pinned['assembly'],pinned['seed']))
            elif route == '/api/rows/export':
                result = workshop.start_export(request)
            elif route == '/api/feedback':
                result = workshop.feedback(request)
            elif route == '/api/jobs/cancel':
                result = workshop.cancel_export(request.get('id'))
            else:
                return self.json_response(dict(error='Unknown endpoint'),404)
            self.json_response(result)
        except (ValueError,KeyError,OSError,TypeError,subprocess.SubprocessError) as exc:
            self.json_response(dict(error=str(exc)),400)

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


class ViewerServer(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('publish').add_argument('build', type=Path)
    commands.add_parser('attach-stl').add_argument('build', type=Path)
    commands.add_parser('serve').add_argument('--port', type=int, default=8765)
    commands.add_parser('piece').add_argument('id')
    args = parser.parse_args()
    if args.command == 'publish':
        print(json.dumps(publish(args.build), indent=2))
    elif args.command == 'attach-stl':
        print(json.dumps(attach_stl(args.build), indent=2))
    elif args.command == 'piece':
        print(json.dumps(piece_ids.lookup(args.id, DATA), indent=2))
    else:
        print(f'Elf review: http://127.0.0.1:{args.port}', flush=True)
        ViewerServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
