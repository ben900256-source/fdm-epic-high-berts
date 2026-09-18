"""Export current modular reviews for measured, explicitly unvalidated trials."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess

from . import formats, validation
from .atelier import file_hash
from .prusa import slice_build, support_audit
from .review import find_blender


def check_union_coverage(result, inputs):
    """An additive union must retain its inputs, allowing only numerical drift."""
    largest = max(item['volume_mm3'] for item in inputs)
    if result['volume_mm3'] < largest-max(0.00001, largest*0.0001):
        raise ValueError('Exact union lost input volume')
    for axis in range(3):
        lower = min(item['bounds_min_mm'][axis] for item in inputs)
        upper = max(item['bounds_max_mm'][axis] for item in inputs)
        if result['bounds_min_mm'][axis] > lower+0.001 or result['bounds_max_mm'][axis] < upper-0.001:
            raise ValueError('Exact union lost input extent')


def restore_model_coordinates(layers, mesh):
    """Undo CLI --center for asymmetric modular equipment overhangs."""
    center = [(min(v[i] for v in mesh.vertices)+max(v[i] for v in mesh.vertices))/2 for i in range(2)]
    for layer in layers:
        layer['paths'] = [(x+center[0], y+center[1], nx+center[0], ny+center[1], width, role)
                          for x,y,nx,ny,width,role in layer['paths']]
    return center


def cached_figure_translations(previous, current):
    """Require five complete translated copies, with unchanged base and poses."""
    old = {p['instance_id']:p for p in previous['placements']}
    first = {key.split('/',1)[1]:p for key,p in old.items() if key.startswith('elf-01/')}
    current_base = {p['instance_id']:p for p in current['placements'] if '/' not in p['instance_id']}
    if current_base != {key:p for key,p in old.items() if '/' not in key}:
        raise ValueError('cached base placement changed')
    translations = []
    seen = set(current_base)
    for index in range(5):
        prefix = f'elf-{index+1:02}/'
        group = {p['instance_id'].split('/',1)[1]:p for p in current['placements'] if p['instance_id'].startswith(prefix)}
        if set(group) != set(first):
            raise ValueError('cached figure must retain every pinned part')
        delta = [group['torso']['mount'][i][3]-first['torso']['mount'][i][3] for i in range(3)]
        for role, placement in group.items():
            original = first[role]
            if {k:v for k,v in placement.items() if k not in ('instance_id','mount')} != {k:v for k,v in original.items() if k not in ('instance_id','mount')}:
                raise ValueError('cached part definition changed')
            for i in range(4):
                for j in range(4):
                    expected = original['mount'][i][j] + (delta[i] if i<3 and j==3 else 0)
                    if abs(placement['mount'][i][j]-expected)>1e-9:
                        raise ValueError('cached equipment or pose alignment changed')
            seen.add(placement['instance_id'])
        if translations and any(abs(delta[i]-translations[0][i]-(4*index if i==0 else 0))>1e-9 for i in range(2)):
            raise ValueError('trial requires uniform 4 mm horizontal figure spacing')
        translations.append(delta)
    if seen != {p['instance_id'] for p in current['placements']}:
        raise ValueError('unexpected trial placements')
    return translations


def publish(output):
    """Display the exported STL itself, independently of the component review."""
    import array
    from datetime import datetime, timezone
    import hashlib
    import math
    import sys
    from .viewer import DATA, _write_json
    output = Path(output).resolve()
    mesh = formats.read_stl(output/'elf-spearman-proof.stl')
    values = array.array('f')
    for triangle in mesh.triangles:
        a, b, c = [mesh.vertices[i] for i in triangle]
        u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        length = math.sqrt(sum(x*x for x in cross))
        if length == 0:
            raise ValueError('degenerate exported triangle')
        normal = [x/length for x in cross]
        for point in (a,b,c):
            values.extend(point)
            values.extend(normal)
    if sys.byteorder != 'little':
        values.byteswap()
    payload = values.tobytes()
    digest = hashlib.sha256(payload).hexdigest()
    (DATA/'assets').mkdir(parents=True, exist_ok=True)
    (DATA/'assets'/f'{digest}.bin').write_bytes(payload)
    job = json.loads((output/'internal/assembly-job.json').read_text())
    definition = file_hash(output/'internal/exact-union-order.json')
    ref = 'manufacturing.spearman-stand@1'
    assembly_id = 'aurelian-spearmen-manufacturing-trial'
    manifest = dict(assembly=dict(schema_version=1, assembly_id=assembly_id,
                    label='Spearmen — fused print trial', placements=[dict(instance_id='stand', part=ref,
                    definition_sha256=definition, mount=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])]),
                    assets={ref:dict(url=f'/data/assets/{digest}.bin', sha256=digest, definition_sha256=definition)},
                    seed=job['seed'], build=output.name, visual_only=True,
                    source_stl_sha256=file_hash(output/'elf-spearman-proof.stl'),
                    label='Exported manufacturing trial; not digitally validated')
    manifest['revision'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    manifest['updated'] = datetime.now(timezone.utc).isoformat()
    key = hashlib.sha256(assembly_id.encode()).hexdigest()
    (DATA/'reviews').mkdir(exist_ok=True)
    _write_json(DATA/'reviews'/f'{key}.json', manifest)
    index = json.loads((DATA/'reviews.json').read_text()) if (DATA/'reviews.json').exists() else dict(reviews=[])
    index['reviews'] = [r for r in index['reviews'] if r['id'] != assembly_id] + [dict(
        id=assembly_id, label=manifest['assembly']['label'], url=f'/data/reviews/{key}.json', revision=manifest['revision'])]
    _write_json(DATA/'reviews.json', index)
    _write_json(DATA/'latest.json', manifest)
    (output/'viewer-review.json').write_text(json.dumps(manifest, indent=2))
    return manifest['revision']


def build(review, output, *, seed, figure_cache=None, sequential_stand=False):
    review, output = Path(review).resolve(), Path(output).resolve()
    job = json.loads((review/'assembly-job.json').read_text())
    if type(seed) is not int or job['seed'] != seed:
        raise ValueError('explicit integer seed must match the pinned review')
    if output.exists():
        raise ValueError('use a fresh output directory')
    blender = find_blender()
    version = subprocess.run([str(blender), '--version'], capture_output=True, text=True, check=True)
    if 'Blender 5.1.2' not in version.stdout:
        raise ValueError('Blender 5.1.2 is required')
    output.mkdir(parents=True)
    (output/'build-inputs.json').write_text(json.dumps(dict(
        seed=seed, review=str(review),
        assembly_job_sha256=file_hash(review/'assembly-job.json'),
        source_scene_sha256=file_hash(review/'assembly.blend'),
        generator_sha256={name:file_hash(Path(__file__).with_name(name)) for name in
                          ('modular_print.py','modular_print_blender.py','modular_print_verify.py','blender_backend.py')}), indent=2))
    command = [str(find_blender()), '--background', str(review/'assembly.blend'),
               '--python-exit-code', '1', '--python', str(Path(__file__).with_name('modular_print_blender.py')),
               '--', str(review), str(output)]
    if figure_cache is not None:
        worker = Path(__file__).with_name('modular_print_cached_sequential.py' if sequential_stand else 'modular_print_cached.py')
        command = [str(blender), '--background', str(review/'assembly.blend'), '--python-exit-code', '1',
                   '--python', str(worker), '--', str(review), str(Path(figure_cache).resolve()), str(output)]
        inputs = json.loads((output/'build-inputs.json').read_text())
        inputs['generator_sha256'][worker.name] = file_hash(worker)
        inputs['generator_sha256']['modular_print_cached.py'] = file_hash(Path(__file__).with_name('modular_print_cached.py'))
        inputs['figure_cache'] = str(Path(figure_cache).resolve())
        (output/'build-inputs.json').write_text(json.dumps(inputs, indent=2))
    with (output/'blender.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=3600)
    verify(output)
    return package(output)


def verify(output):
    output = Path(output).resolve()
    command = [str(find_blender()), '--background', str(output/'internal/elf-spearman-proof.blend'),
               '--python-exit-code', '1', '--python', str(Path(__file__).with_name('modular_print_verify.py')),
               '--', str(output)]
    with (output/'internal/manufacturing-provenance.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)


def package(output):
    output = Path(output)
    mesh = formats.read_stl(output/'elf-spearman-proof.stl')
    indexed = formats.sanitize_stl_mesh(mesh)
    analysis = validation.analyze_mesh(indexed.mesh)
    topology = asdict(analysis)
    topology.update(watertight=analysis.watertight, manifold=analysis.manifold,
                    outward_facing=analysis.outward_facing, positive_volume=analysis.positive_volume)
    formats.write_3mf(output/'elf-spearman-proof.3mf', [formats.ColorVolume(
        'Current modular spearmen - trial', mesh, formats.Material('Single-color PLA', '#D2C5A2'))])
    result = dict(label='manufacturing trial; not digitally validated', digitally_validated=False,
                  topology=topology, removed_triangles=indexed.removed_triangle_count,
                  stl_sha256=file_hash(output/'elf-spearman-proof.stl'))
    (output/'modular-print.json').write_text(json.dumps(result, indent=2))
    return result


def compare(output, repeat):
    output, repeat = Path(output).resolve(), Path(repeat).resolve()
    if output == repeat:
        raise ValueError('comparison requires an independent build directory')
    left = json.loads((output/'internal/mesh-metrics.json').read_text())
    right = json.loads((repeat/'internal/mesh-metrics.json').read_text())
    jobs = [json.loads((folder/'internal/assembly-job.json').read_text()) for folder in (output, repeat)]
    checks = dict(seed=left['seed'] == right['seed'] == jobs[0]['seed'] == jobs[1]['seed'],
                  pinned_assembly=jobs[0]['assembly'] == jobs[1]['assembly'],
                  mesh_hash=left['mesh_hash'] == right['mesh_hash'],
                  stl=file_hash(output/'elf-spearman-proof.stl') == file_hash(repeat/'elf-spearman-proof.stl'),
                  operation_order=file_hash(output/'internal/exact-union-order.json') == file_hash(repeat/'internal/exact-union-order.json'))
    result = dict(passes=all(checks.values()), checks=checks, repeat=str(repeat),
                  method='independent same-seed Exact fusion of pinned immutable component caches')
    (output/'geometry-comparison.json').write_text(json.dumps(result, indent=2))
    return result


def assess(output, automatic_supports=False):
    from .regiment_validation import parse_gcode, inspect_layers
    from .printability import assess_toolpaths, deposition_mask, model_paths, pixel
    output = Path(output)
    previews = output/'previews'
    previews.mkdir(exist_ok=True)
    mesh = formats.read_stl(output/'elf-spearman-proof.stl')
    layers, gcode = parse_gcode((output/'elf-spearman-proof.gcode').read_text())
    gcode['source_xy_center_mm'] = restore_model_coordinates(layers, mesh)
    contours = inspect_layers(mesh, layers, previews)
    support = assess_toolpaths(layers, previews)
    job = json.loads((output/'internal/assembly-job.json').read_text())
    faces, masks = [], {}
    for placement in job['assembly']['placements']:
        if not placement['instance_id'].endswith('/head'):
            continue
        landmarks = job['assets'][placement['part']]['definition']['parameters']['landmarks']
        for role, solid in [('left_eye_socket', False), ('right_eye_socket', False),
                            ('mouth_line', False), ('nose_bridge', True), ('integrated_brow', True)]:
            local = landmarks[role]
            world = [sum(placement['mount'][i][j]*local[j] for j in range(3))+placement['mount'][i][3] for i in range(3)]
            index = next((i for i, layer in enumerate(layers) if layer['z'] >= world[2]), None)
            count = None
            if index is not None:
                if index not in masks:
                    masks[index] = deposition_mask(model_paths(layers[index]))
                x, y = pixel(world[:2])
                count = sum(bool(masks[index].getpixel(p)) for p in [(x,y),(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
            faces.append(dict(instance_id=placement['instance_id'], feature=role, world_mm=world,
                              layer_index=index, deposited_samples=count, expected_solid=solid,
                              passes=count is not None and (count >= 3 if solid else count <= 2)))
    (previews/'face-layer-evidence.json').write_text(json.dumps(dict(
        method='five deposited raster witnesses at pinned modular head landmarks',
        passes=bool(faces) and all(f['passes'] for f in faces), features=faces), indent=2))
    result = dict(label='manufacturing trial; not digitally validated', passes=False,
                  mesh_layer_checks=contours['passes'], deposited_layer_support=support['passes'],
                  face_details_survive=bool(faces) and all(f['passes'] for f in faces),
                  support_summary=support['summary'], gcode=gcode,
                  remaining_validation=['evaluated structural dimensions and spacing', 'physical trial'],
                  stl_sha256=file_hash(output/'elf-spearman-proof.stl'),
                  gcode_sha256=file_hash(output/'elf-spearman-proof.gcode'))
    if automatic_supports:
        result['automatic_support_audit'] = support_audit(output)
    (output/'printability-review.json').write_text(json.dumps(result, indent=2))
    checks = [('Sliced contour coverage', result['mesh_layer_checks']),
              ('Deposited-layer support', result['deposited_layer_support']),
              ('Facial landmark survival', result['face_details_survive'])]
    (output/'PRINT-TRIAL.md').write_text(
        '# Current spearman stand — physical trial\n\n'
        '**Not digitally validated.** Inspect the failed checks below before attempting a print.\n\n'
        'Open `elf-spearman-proof-prusa.3mf` as a project in PrusaSlicer 2.9.6. '
        'It contains the exported stand and the saved five-tool Prusa XL profile: '
        'tool 2, 0.25 mm nozzle, PLA, 0.05 mm layers, 0.14 mm first layer and 6 mm brim. '
        'The nozzle array is `0.4,0.25,0.4,0.4,0.4`. The project was reopened and sliced without an external configuration.\n\n'
        'The main G-code has no removable supports. Files in `support-audit/` are diagnostics, '
        'not the trial print.\n\n' +
        '\n'.join(f'- {name}: {"pass" if passed else "FAIL"}' for name, passed in checks) +
        '\n\nSee `printability-review.json`, `modular-print.json` and `previews/` for the measured evidence. '
        'Complete structural and spacing validation is still required before calling this print ready.\n\n'
        'The 20 × 5 × 2 mm base has two bottom-open pockets for 3 × 1 mm magnets. '
        'Pocket diameter is 3.2 mm and depth is 1.1 mm; glue magnets in after printing. '
        'Those fit allowances have not been physically tested.\n\n'
        'For the physical trial, inspect missing face and chainmail detail, unsupported undersides, '
        'spear tips, boot contact, magnet fit and handling strength. Record observations before changing the recipes.\n',
        encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--no-slice', action='store_true')
    parser.add_argument('--figure-cache', type=Path, help='prior build containing a checked elf-01 and base')
    parser.add_argument('--sequential-stand', action='store_true')
    args = parser.parse_args()
    build(args.review, args.output, seed=args.seed, figure_cache=args.figure_cache, sequential_stand=args.sequential_stand)
    publish(args.output)
    if not args.no_slice:
        slice_build(args.output)
        print(json.dumps(assess(args.output, automatic_supports=True)))


if __name__ == '__main__':
    main()
