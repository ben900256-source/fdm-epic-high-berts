"""Compose cached visual parts; compile only missing or changed definitions."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from .components.core import component_digest
from .components.parts import catalog, cache_key, isolated_part, resolve_assembly
from .army import load_assembly
from .review import find_blender

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE = ROOT/'out/part-cache'


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def engine_hash():
    package = Path(__file__).parent
    return component_digest({name: file_hash(package/name) for name in
                             ('atelier_blender.py', 'regiment_blender.py', 'blender_backend.py')})


def prepare(data, *, seed, cache=DEFAULT_CACHE, definitions=None):
    if type(seed) is not int:
        raise ValueError("seed must be an explicit integer")
    definitions = catalog() if definitions is None else definitions
    assembly = resolve_assembly(data, definitions)
    engine = engine_hash()
    assets = {}
    for item in assembly['placements']:
        ref = item['part']
        if ref in assets:
            continue
        definition = definitions[ref]
        key = cache_key(definition, engine)
        directory = Path(cache).resolve()/key
        manifest = directory/'asset.json'
        record = None
        if manifest.exists():
            record = json.loads(manifest.read_text())
            if (record['key'] != key or record['definition_sha256'] != definition.sha256 or
                    record['blend_sha256'] != file_hash(directory/'part.blend')):
                raise ValueError(f"cached part failed integrity check: {ref}; use a fresh cache directory")
        elif directory.exists():
            raise ValueError(f"incomplete cache entry: {directory}; use a fresh cache directory")
        assets[ref] = dict(key=key, directory=str(directory), definition=definition.to_dict(),
                           cached=record is not None, manifest=record)
    return dict(assembly=assembly, seed=seed, engine_hash=engine, assets=assets)


def compose(data, *, seed, output, cache=DEFAULT_CACHE, render=False, definitions=None):
    started = time.perf_counter()
    job = prepare(data, seed=seed, cache=cache, definitions=definitions)
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh output directory; earlier review scenes are preserved")
    output.mkdir(parents=True, exist_ok=True)
    job.update(output=str(output), render=render)
    path = output/'assembly-job.json'
    path.write_text(json.dumps(job, indent=2)+'\n')
    blender = find_blender()
    if blender is None:
        raise ValueError("Blender 5.1.2 is required")
    version = subprocess.run([str(blender), '--version'], capture_output=True, text=True, timeout=30)
    if 'Blender 5.1.2' not in version.stdout:
        raise ValueError("Blender 5.1.2 is required")
    entry = Path(__file__).with_name('atelier_blender.py')
    with (output/'atelier.log').open('w') as log:
        process = subprocess.run([str(blender), '--background', '--factory-startup', '--python-exit-code', '1',
                                  '--python', str(entry), '--', 'compose', str(path)],
                                 stdout=log, stderr=subprocess.STDOUT, timeout=600)
    if process.returncode:
        raise RuntimeError(f"visual assembly failed; see {output/'atelier.log'}")
    with (output/'provenance.log').open('w') as log:
        check = subprocess.run([str(blender), '--background', str(output/'assembly.blend'),
                                '--python-exit-code', '1', '--python', str(entry), '--', 'verify', str(path)],
                               stdout=log, stderr=subprocess.STDOUT, timeout=120)
    if check.returncode:
        raise RuntimeError(f"saved part provenance failed; see {output/'provenance.log'}")
    result = json.loads((output/'visual-review.json').read_text())
    result['elapsed_seconds'] = round(time.perf_counter()-started, 3)
    (output/'visual-review.json').write_text(json.dumps(result, indent=2)+'\n')
    from .viewer import publish
    result['browser_review'] = publish(output)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list', help='list reusable part revisions without starting Blender')
    for name in ('part', 'compose', 'plan'):
        command = commands.add_parser(name)
        command.add_argument('input', help='part@revision for part; assembly JSON for compose/plan')
        command.add_argument('--seed', type=int, required=True)
        command.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
        if name != 'plan':
            command.add_argument('--output', type=Path, required=True)
            command.add_argument('--render', action='store_true', help='optional single PNG; off by default')
    args = parser.parse_args(argv)
    try:
        if args.command == 'list':
            result = [dict(part=d.reference, name=d.name, family=d.family) for d in catalog().values()]
        else:
            data = isolated_part(args.input) if args.command == 'part' else load_assembly(args.input)
            if args.command == 'plan':
                job = prepare(data, seed=args.seed, cache=args.cache)
                result = dict(compile=[ref for ref, a in job['assets'].items() if not a['cached']],
                              reuse=[ref for ref, a in job['assets'].items() if a['cached']],
                              placements=len(job['assembly']['placements']))
            else:
                result = compose(data, seed=args.seed, output=args.output, cache=args.cache, render=args.render)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        print(json.dumps(dict(error=str(exc))))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
