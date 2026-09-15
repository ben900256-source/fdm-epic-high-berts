"""Reuse a checked figure and base for an identical five-figure trial stand."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt import blender_backend as bb
from fdm_sculpt.atelier_blender import verify
from fdm_sculpt.modular_print_blender import ordered_fuse
from fdm_sculpt.modular_print import cached_figure_translations


def run(review, cache_build, output):
    review, cache_build, output = map(Path, (review, cache_build, output))
    internal = output/'internal'
    internal.mkdir()
    job = json.loads((review/'assembly-job.json').read_text())
    job['output'] = str(internal)
    verify(job)
    manifests = json.loads(bpy.context.scene['asset_manifest_json'])
    for ref, asset in job['assets'].items():
        asset['manifest'] = manifests[ref]
    cached_inputs = json.loads((cache_build/'build-inputs.json').read_text())
    cached_review = Path(cached_inputs['review'])
    assert bb._sha256_file(cached_review/'assembly-job.json') == cached_inputs['assembly_job_sha256']
    previous = json.loads((cached_review/'assembly-job.json').read_text())
    assert previous['seed'] == job['seed']
    translations = cached_figure_translations(previous['assembly'], job['assembly'])
    record_path = cache_build/'figure-cache.json'
    if record_path.exists():
        record = json.loads(record_path.read_text())
        cache = cache_build/record['scene']
        assert bb._sha256_file(cache) == record['scene_sha256']
        assert record['seed'] == job['seed']
        names = [record['base_object'], record['figure_object']]
    else:
        cache = cache_build/'internal/union-failure.blend'
        names = ['fused-base', 'fused-elf-01/join-20']
    with bpy.data.libraries.load(str(cache.resolve()), link=False) as (_, data):
        data.objects = names
    source = bpy.data.collections.new('MANUFACTURING_OPERANDS')
    bpy.context.scene.collection.children.link(source)
    for obj in data.objects:
        source.objects.link(obj)
        metrics = bb._object_metrics(obj)
        assert metrics['artifact_preflight']['passes'] and bb._self_intersection_count(obj) == 0
    base, figure = data.objects
    objects = [base]
    for index in range(5):
        obj = figure.copy()
        obj.data = figure.data.copy()
        obj.name = f'cached-elf-{index+1:02}'
        source.objects.link(obj)
        obj.matrix_world = Matrix.Translation(translations[index]) @ figure.matrix_world
        objects.append(obj)
    bpy.context.scene['manufacturing_output_directory'] = str(internal)
    print('FUSING_FIVE_IDENTICAL_SPEARMEN', flush=True)
    master = ordered_fuse('Spearman trial stand', objects, source, preserve_vertices=True, small_closure=True)
    target = bpy.data.collections['EVALUATED_EXPORT']
    source.objects.unlink(master)
    target.objects.link(master)
    order = [o.name for o in objects]
    master['exact_union_order_json'] = json.dumps(order)
    master['role'] = 'fused_printable_strip'
    master['seed'] = job['seed']
    source.hide_viewport = source.hide_render = True
    bpy.data.collections['VISUAL_PREVIEW'].hide_viewport = True
    bpy.data.collections['VISUAL_PREVIEW'].hide_render = True
    bpy.context.scene['regiment_mode'] = 'modular-manufacturing-trial'
    bpy.context.scene['digitally_validated'] = False
    metrics = bb._object_metrics(master)
    metrics.update(seed=job['seed'], self_intersection_count=bb._self_intersection_count(master))
    (internal/'assembly-job.json').write_text(json.dumps(job, indent=2))
    (internal/'exact-union-order.json').write_text(json.dumps(order, indent=2))
    operations = {o.name:json.loads(o['manufacturing_operation_json']) for o in objects+[master]}
    (internal/'manufacturing-operations.json').write_text(json.dumps(operations, indent=2, sort_keys=True))
    evidence = dict(source_build=str(cache_build.resolve()), source_scene_sha256=bb._sha256_file(cache),
                    source_inputs=cached_inputs, placement_contract='five exact copies of elf-01, X spacing 4 mm',
                    figure_translations_mm=translations,
                    cached_base_and_figure_pass_full_topology_and_intersection_checks=True)
    (internal/'manufacturing-cache.json').write_text(json.dumps(evidence, indent=2))
    bpy.context.scene['manufacturing_cache_json'] = json.dumps(evidence, sort_keys=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(internal/'elf-spearman-proof.blend'))
    bpy.ops.file.make_paths_relative()
    bpy.ops.file.pack_all()
    bpy.ops.file.pack_libraries()
    bpy.ops.wm.save_as_mainfile(filepath=str(internal/'elf-spearman-proof.blend'))
    bb._export_stl(output/'elf-spearman-proof.stl', [master])
    metrics['stl_sha256'] = bb._sha256_file(output/'elf-spearman-proof.stl')
    (internal/'mesh-metrics.json').write_text(json.dumps(metrics, indent=2))
    print('MODULAR_PRINT_COMPLETE', flush=True)


if __name__ == '__main__':
    run(*sys.argv[sys.argv.index('--')+1:])
