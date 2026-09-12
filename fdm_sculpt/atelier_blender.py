"""Blender worker: cache local parts once, place collection instances cheaply."""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt import blender_backend as bb
from fdm_sculpt.components.core import ComponentDefinition


def mesh_hash(obj):
    digest = hashlib.sha256()
    for row in obj.matrix_basis:
        digest.update(struct.pack('<4f', *row))
    for vertex in obj.data.vertices:
        digest.update(struct.pack('<3f', *vertex.co))
    for face in obj.data.polygons:
        digest.update(struct.pack('<I', len(face.vertices)))
        digest.update(struct.pack('<'+'I'*len(face.vertices), *face.vertices))
    return digest.hexdigest()


def compile_missing(job):
    missing = [a for a in job['assets'].values() if not a['cached']]
    if not missing:
        return
    from fdm_sculpt.regiment_blender import ElfBuilder
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bb._configure_scene(bpy.context.scene, 1000)
    context = bb._BuildContext(bpy.context.scene)
    parts, deferred = [], []
    for asset in missing:
        definition = ComponentDefinition.from_dict(asset['definition'])
        part = dict(part_id=asset['key'][:20], kind='reusable-visual-part', variant=definition.reference, position=[0,0,0])
        initial = context.begin_part(part)
        builder = ElfBuilder(context, part, initial.collection)
        objects = {}
        p = definition.to_dict()['parameters']
        for atom in p['atoms']:
            args = dict(atom)
            role, primitive = args.pop('role'), args.pop('primitive')
            obj = builder.recipe_atom(role, primitive, 'ivory', args)
            for key, value in dict(component_id=definition.component_id, component_version=definition.version,
                                   component_definition_sha256=definition.sha256, component_geometry_role=role).items():
                obj[key] = value
            objects[role] = obj
        deferred.extend((builder, objects[o['target']], objects[o['operand']], o['operation']) for o in p['operations'])
        source = initial.collection
        source.name = 'PART_SOURCE_'+asset['key']
        source['definition_json'] = json.dumps(definition.to_dict(), sort_keys=True)
        source['operation_order_json'] = json.dumps(p['operations'])
        source['landmarks_json'] = json.dumps(p['landmarks'])
        parts.append((asset, definition, source, objects))
    for builder, target, operand, operation in deferred:
        bb._PartBuilder.boolean(builder, target, operand, operation)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    # Evaluate all local details once; no cross-part Booleans exist here.
    for asset, definition, source, objects in parts:
        visual = bpy.data.collections.new('PART_VISUAL_'+asset['key'])
        visual['definition_sha256'] = definition.sha256
        visual.asset_mark()
        visual.asset_data.description = definition.reference+' — visual part, local mount, not print validated'
        hashes = {}
        for role in definition.output_roles:
            original = objects[role]
            mesh = bpy.data.meshes.new_from_object(original.evaluated_get(depsgraph), depsgraph=depsgraph)
            obj = bpy.data.objects.new('visual_'+asset['key'][:16]+'_'+role, mesh)
            obj.matrix_world = original.matrix_world.copy()
            for key in original.keys():
                obj[key] = original[key]
            obj['export_geometry'] = False
            visual.objects.link(obj)
            hashes[role] = mesh_hash(obj)
        source.hide_viewport = True
        source.hide_render = True
        directory = Path(asset['directory'])
        directory.mkdir(parents=True, exist_ok=False)
        blend = directory/'part.blend'
        bpy.data.libraries.write(str(blend), {source, visual}, fake_user=True)
        record = dict(key=asset['key'], definition_sha256=definition.sha256,
                      source_collection=source.name, visual_collection=visual.name, mesh_hashes=hashes,
                      blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest())
        (directory/'definition.json').write_text(json.dumps(definition.to_dict(), indent=2)+'\n')
        (directory/'asset.json').write_text(json.dumps(record, indent=2)+'\n')
        asset['manifest'] = record
        print('PART_COMPILED '+definition.reference, flush=True)


def assemble(job):
    compile_missing(job)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bb._configure_scene(scene, 1200)
    visible = bpy.data.collections.new('VISUAL_PREVIEW')
    source_root = bpy.data.collections.new('SOURCE_PRIMITIVES')
    export = bpy.data.collections.new('EVALUATED_EXPORT')
    for collection in (visible, source_root, export):
        scene.collection.children.link(collection)
    source_root.hide_viewport = source_root.hide_render = True
    loaded = {}
    for ref, asset in job['assets'].items():
        record = asset['manifest']
        with bpy.data.libraries.load(str(Path(asset['directory'])/'part.blend'), link=True) as (available, requested):
            requested.collections = [record['source_collection'], record['visual_collection']]
        loaded[ref] = requested.collections
    bounds = []
    for placement in job['assembly']['placements']:
        source, visual = loaded[placement['part']]
        mount = Matrix(placement['mount'])
        for collection, target, prefix in ((visual, visible, ''), (source, source_root, 'source/')):
            obj = bpy.data.objects.new(prefix+placement['instance_id'], None)
            obj.instance_type, obj.instance_collection = 'COLLECTION', collection
            obj.matrix_world = mount
            obj['part_reference'] = placement['part']
            obj['definition_sha256'] = placement['definition_sha256']
            target.objects.link(obj)
        for obj in visual.objects:
            bounds.extend(mount @ obj.matrix_basis @ Vector(corner) for corner in obj.bound_box)
    low = Vector([min(p[i] for p in bounds) for i in range(3)])
    high = Vector([max(p[i] for p in bounds) for i in range(3)])
    center, size = (low+high)/2, max(high-low)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.region_3d.view_distance = size*1.5
                space.region_3d.view_location = center
                space.region_3d.view_rotation = Vector((0.6,-1.8,0.7)).to_track_quat('Z','Y')
                space.clip_end = 1000
                space.clip_start = 0.01
                space.shading.type = 'SOLID'
                space.shading.color_type = 'MATERIAL'
                space.shading.show_cavity = True
                space.overlay.show_floor = False
                space.overlay.show_extras = False
    scene['regiment_mode'] = 'modular-visual-preview'
    scene['digitally_validated'] = False
    scene['assembly_json'] = json.dumps(job['assembly'], sort_keys=True)
    scene['seed'] = job['seed']
    scene['asset_manifest_json'] = json.dumps({ref: a['manifest'] for ref,a in job['assets'].items()}, sort_keys=True)
    output = Path(job['output'])
    if job['render']:
        camera = bb._ensure_camera(scene)
        direction = Vector((0.6,-1.8,0.7)).normalized()
        camera.location = center+direction*100
        camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale = size*1.25
        scene.render.filepath = str(output/'preview.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'assembly.blend'))
    if job['render']:
        bpy.ops.render.render(write_still=True)
    (output/'visual-review.json').write_text(json.dumps(dict(
        mode='modular-visual-preview', digitally_validated=False, assembly=str(output/'assembly.blend'),
        compiled_parts=[ref for ref,a in job['assets'].items() if not a['cached']],
        reused_parts=[ref for ref,a in job['assets'].items() if a['cached']],
        placements=len(job['assembly']['placements']), rendered=job['render'],
        label='visual-only assembly of reusable parts; no manufacturing build'), indent=2)+'\n')
    print('ATELIER_ASSEMBLY_COMPLETE', flush=True)


def verify(job):
    scene = bpy.context.scene
    checks = dict(assembly=json.loads(scene['assembly_json']) == job['assembly'],
                  visual_only=scene['digitally_validated'] is False and not list(bpy.data.collections['EVALUATED_EXPORT'].all_objects),
                  hidden_sources=bpy.data.collections['SOURCE_PRIMITIVES'].hide_viewport)
    manifests = json.loads(scene['asset_manifest_json'])
    for ref, asset in job['assets'].items():
        definition = ComponentDefinition.from_dict(asset['definition'])
        record = manifests[ref]
        source = bpy.data.collections[record['source_collection']]
        visual = bpy.data.collections[record['visual_collection']]
        valid = json.loads(source['definition_json']) == definition.to_dict()
        atoms = {o['component_geometry_role']: o for o in source.objects}
        p = definition.to_dict()['parameters']
        valid = valid and len(atoms) == len(p['atoms'])
        for atom in p['atoms']:
            obj = atoms[atom['role']]
            valid = valid and obj['component_definition_sha256'] == definition.sha256
            expected = [op for op in p['operations'] if op['target'] == atom['role']]
            booleans = [m for m in obj.modifiers if m.type == 'BOOLEAN']
            valid = valid and len(expected) == len(booleans)
            for op, modifier in zip(expected, booleans):
                valid = valid and modifier.solver == 'EXACT' and modifier.operation == op['operation'] and modifier.object == atoms[op['operand']]
        valid = valid and {o['component_geometry_role']: mesh_hash(o) for o in visual.objects} == record['mesh_hashes']
        checks[ref] = bool(valid)
    for placement in job['assembly']['placements']:
        obj = bpy.data.objects[placement['instance_id']]
        checks[placement['instance_id']] = (obj.instance_collection.name == manifests[placement['part']]['visual_collection'] and
            all(abs(obj.matrix_basis[i][j]-placement['mount'][i][j]) < 1e-5 for i in range(4) for j in range(4)))
    result = dict(passes=all(checks.values()), checks=checks,
                  method='reopened scene; pinned local recipes, Exact operands, cached meshes and instance transforms')
    (Path(job['output'])/'saved-provenance.json').write_text(json.dumps(result, indent=2)+'\n')
    if not result['passes']:
        raise ValueError('saved modular provenance failed: '+str([k for k,v in checks.items() if not v]))
    print('ATELIER_PROVENANCE_VERIFIED', flush=True)


if __name__ == '__main__':
    command, path = sys.argv[sys.argv.index('--')+1:]
    job = json.loads(Path(path).read_text())
    (assemble if command == 'compose' else verify)(job)
