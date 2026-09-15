"""Materialize a saved modular review through reproducible Exact unions."""
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt import blender_backend as bb
from fdm_sculpt.atelier_blender import verify
from fdm_sculpt.modular_print import check_union_coverage


def tessellated_copy(original, collection):
    work = original.copy()
    work.data = original.data.copy()
    collection.objects.link(work)
    triangulate = work.modifiers.new('cached_surface_tessellation', 'TRIANGULATE')
    triangulate.ngon_method = triangulate.quad_method = 'BEAUTY'
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(work.evaluated_get(graph), depsgraph=graph)
    result = bpy.data.objects.new('tessellated-' + original.name, mesh)
    collection.objects.link(result)
    result.matrix_world = work.matrix_world.copy()
    bpy.data.objects.remove(work, do_unlink=True)
    return result


def fuse(name, objects, collection, *, numerical_weld_mm=0.00025, resolve_self=True, native_tessellation=True, hole_tolerant=True):
    """Exact union with native tessellation before numerical closure."""
    inputs = []
    for original in objects:
        if native_tessellation:
            item = tessellated_copy(original, collection)
        else:
            item = original.copy()
            item.data = original.data.copy()
            collection.objects.link(item)
        inputs.append(item)
    work = inputs[0]
    operands = None
    if len(objects) > 1:
        operands = bpy.data.collections.new('exact-operands-' + name)
        bpy.context.scene.collection.children.link(operands)
        for obj in inputs[1:]:
            operands.objects.link(obj)
        union = work.modifiers.new('01_exact_union', 'BOOLEAN')
        union.operation = 'UNION'
        union.solver = 'EXACT'
        union.operand_type = 'COLLECTION'
        union.collection = operands
        union.use_self = resolve_self
        union.use_hole_tolerant = hole_tolerant
    if native_tessellation:
        triangulate = work.modifiers.new('02_union_tessellation', 'TRIANGULATE')
        triangulate.ngon_method = triangulate.quad_method = 'BEAUTY'
    weld = work.modifiers.new('02_declared_numerical_closure', 'WELD')
    weld.merge_threshold = numerical_weld_mm
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = work.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
    mesh.validate(clean_customdata=False)
    mesh.update(calc_edges=True)
    result = bpy.data.objects.new(name, mesh)
    collection.objects.link(result)
    result.matrix_world = work.matrix_world.copy()
    result['manufacturing_operation_json'] = json.dumps(dict(
        operation='UNION', solver='EXACT', self_intersections=resolve_self,
        hole_tolerant=hole_tolerant, native_tessellation=native_tessellation,
        numerical_weld_mm=numerical_weld_mm, operands=[o.name for o in objects]))
    for obj in inputs:
        bpy.data.objects.remove(obj, do_unlink=True)
    if operands is not None:
        bpy.data.collections.remove(operands)
    metrics = bb._object_metrics(result, preflight_artifact=False, include_mesh_hash=False)
    if not metrics['manifold']:
        raise ValueError(f"Non-manifold manufacturing union {name}: {metrics['nonmanifold_edge_count']} edges")
    check_union_coverage(metrics, [bb._object_metrics(o, preflight_artifact=False, include_mesh_hash=False) for o in objects])
    return result


def ordered_fuse(name, objects, collection, *, small_closure=False, preserve_vertices=False):
    """Try fixed Exact evaluation modes; every candidate faces identical gates."""
    attempts = []
    options = [(True,True,.00025),(False,False,.00001),(False,True,.00001),(True,False,.00025)]
    if small_closure:
        options = [(True,True,.00001), (True,False,.00001)] + options
    if preserve_vertices:
        options = [(True,False,5e-7), (False,False,0), (False,True,0), (True,False,0)] + options
    for index, (native, resolve_self, tolerance) in enumerate(options):
        print('EXACT_MODE', name, native, resolve_self, tolerance, flush=True)
        metrics = None
        try:
            result = fuse(name, objects, collection, native_tessellation=native,
                          resolve_self=resolve_self, numerical_weld_mm=tolerance)
            metrics = bb._object_metrics(result)
            metrics['self_intersection_count'] = bb._self_intersection_count(result)
            if not metrics['artifact_preflight']['passes'] or metrics['self_intersection_count']:
                raise ValueError('export topology or self-intersection check failed')
            result['evaluation_attempts_json'] = json.dumps(attempts)
            return result
        except ValueError as exc:
            print('EXACT_REJECTED', name, str(exc), flush=True)
            attempts.append(dict(native_tessellation=native, resolve_self=resolve_self,
                                 numerical_weld_mm=tolerance, error=str(exc), metrics=metrics))
            result = bpy.data.objects.get(name)
            if index < len(options)-1:
                if result is not None:
                    mesh = result.data
                    bpy.data.objects.remove(result, do_unlink=True)
                    if mesh.users == 0:
                        bpy.data.meshes.remove(mesh)
                continue
            folder = Path(bpy.context.scene['manufacturing_output_directory'])
            (folder/'failed-union.json').write_text(json.dumps(dict(name=name, attempts=attempts, metrics=metrics), indent=2))
            bpy.ops.wm.save_as_mainfile(filepath=str(folder/'union-failure.blend'))
            raise ValueError(f'No checked Exact evaluation passed for {name}') from exc


def fuse_figure(name, objects, collection):
    """Join connected components from the torso outward, checking every join."""
    roles = ['torso', 'skirt', 'left-leg', 'right-leg', 'cape', 'head', 'helmet',
             'shield', 'equipment-joins', 'spear', 'right-arm', 'right-tunic',
             'left-arm', 'left-tunic', 'shield-insignia', 'mail', 'crest']
    def rank(obj):
        role = json.loads(obj['placement_json'])['instance_id'].split('/', 1)[1]
        return roles.index(role) if role in roles else len(roles)
    inputs = sorted(objects, key=rank)
    result = inputs[0]
    for index, operand in enumerate(inputs[1:], 1):
        print('FUSING_JOIN', name, index, operand.name, flush=True)
        result = ordered_fuse(f'{name}/join-{index:02}', [result, operand], collection)
    result['figure_operand_order_json'] = json.dumps([o.name for o in inputs])
    return result


def run(review, output):
    review, output = Path(review), Path(output)
    internal = output / 'internal'
    internal.mkdir(parents=True, exist_ok=False)
    job = json.loads((review / 'assembly-job.json').read_text())
    job['output'] = str(internal)
    verify(job)
    manifests = json.loads(bpy.context.scene['asset_manifest_json'])
    for ref, asset in job['assets'].items():
        asset['manifest'] = manifests[ref]
    scene = bpy.context.scene
    scene['manufacturing_output_directory'] = str(internal.resolve())
    source = bpy.data.collections.new('MANUFACTURING_OPERANDS')
    scene.collection.children.link(source)
    target = bpy.data.collections['EVALUATED_EXPORT']
    groups = {}
    order = []
    parts = {}
    for placement in job['assembly']['placements']:
        instance = bpy.data.objects[placement['instance_id']]
        group = placement['instance_id'].split('/')[0] if '/' in placement['instance_id'] else 'base'
        ref = placement['part']
        if ref not in parts:
            local = []
            for original in sorted(instance.instance_collection.objects, key=lambda o: o.name):
                if original.type != 'MESH':
                    continue
                obj = bpy.data.objects.new(ref + '/' + original.name, original.data.copy())
                source.objects.link(obj)
                obj.data.transform(original.matrix_basis)
                obj['component_geometry_role'] = original.get('component_geometry_role', original.name)
                local.append(obj)
                order.append(obj.name)
            print('FUSING_PART', ref, len(local), flush=True)
            parts[ref] = ordered_fuse('print-' + ref, local, source)
        obj = bpy.data.objects.new(placement['instance_id'], parts[ref].data.copy())
        source.objects.link(obj)
        obj.data.transform(instance.matrix_world)
        obj['placement_json'] = json.dumps(placement, sort_keys=True)
        groups.setdefault(group, []).append(obj)
        order.append(placement['instance_id'])
    fused = []
    bpy.ops.wm.save_as_mainfile(filepath=str(internal / 'prepared-parts.blend'))
    for name, objects in groups.items():
        print('FUSING', name, len(objects), flush=True)
        fused.append(fuse_figure('fused-' + name, objects, source) if name.startswith('elf-')
                     else ordered_fuse('fused-' + name, objects, source))
    print('FUSING_STAND', flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(internal / 'parts-checkpoint.blend'))
    master = ordered_fuse('Spearman trial stand', fused, source)
    source.objects.unlink(master)
    target.objects.link(master)
    master['construction'] = 'ordered Exact unions with recorded tessellation and numerical closure'
    master['role'] = 'fused_printable_strip'
    master['exact_union_order_json'] = json.dumps(order)
    master['seed'] = job['seed']
    source.hide_viewport = source.hide_render = True
    bpy.data.collections['VISUAL_PREVIEW'].hide_viewport = True
    bpy.data.collections['VISUAL_PREVIEW'].hide_render = True
    scene['regiment_mode'] = 'modular-manufacturing-trial'
    scene['digitally_validated'] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(internal / 'fusion-checkpoint.blend'))
    metrics = bb._object_metrics(master)
    metrics['self_intersection_count'] = bb._self_intersection_count(master)
    metrics['seed'] = job['seed']
    print('MEASURED', json.dumps(metrics), flush=True)
    (internal / 'mesh-metrics.json').write_text(json.dumps(metrics, indent=2))
    (internal / 'assembly-job.json').write_text(json.dumps(job, indent=2))
    (internal / 'exact-union-order.json').write_text(json.dumps(order, indent=2))
    operations = {o.name: json.loads(o['manufacturing_operation_json'])
                  for o in source.objects if 'manufacturing_operation_json' in o}
    operations[master.name] = json.loads(master['manufacturing_operation_json'])
    (internal / 'manufacturing-operations.json').write_text(json.dumps(operations, indent=2, sort_keys=True))
    # Pack cached component dependencies into this standalone manufacturing scene.
    bpy.ops.file.make_paths_relative()
    bpy.ops.file.pack_all()
    bpy.ops.file.pack_libraries()
    bpy.ops.wm.save_as_mainfile(filepath=str(internal / 'elf-spearman-proof.blend'))
    bb._export_stl(output / 'elf-spearman-proof.stl', [master])
    metrics['stl_sha256'] = bb._sha256_file(output / 'elf-spearman-proof.stl')
    (internal / 'mesh-metrics.json').write_text(json.dumps(metrics, indent=2))
    (internal / 'assembly-job.json').write_text(json.dumps(job, indent=2))
    (internal / 'exact-union-order.json').write_text(json.dumps(order, indent=2))
    print('MODULAR_PRINT_COMPLETE', flush=True)


if __name__ == '__main__':
    run(*sys.argv[sys.argv.index('--') + 1:])
