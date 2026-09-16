"""One Blender Manifold Boolean Union and native STL export, without validation."""
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Matrix

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from fdm_sculpt.atelier_blender import compile_missing


def export_sleeve(source):
    """Evaluate the pinned sleeve CSG with the export solver on temporary copies.

    The visual Exact cache can contain coincident slivers around cloth creases
    that Manifold refuses as inputs. Preserve every primitive, transform and
    Boolean operation; use Manifold for the local sleeve operations as well as
    the row union. Reviewed definitions and immutable visual caches stay intact.
    """
    staging=bpy.data.collections.new('EXPORT_SLEEVE_STAGING')
    bpy.context.scene.collection.children.link(staging)
    copies={}
    try:
        for original in source.objects:
            obj=original.copy()
            obj.data=original.data.copy()
            obj.matrix_world=original.matrix_basis
            obj.hide_viewport=obj.hide_render=False
            staging.objects.link(obj)
            copies[original]=obj
        for obj in copies.values():
            for modifier in obj.modifiers:
                if modifier.type=='BOOLEAN':
                    modifier.object=copies[modifier.object]
                    modifier.solver='MANIFOLD'
        target=next(o for o in copies.values() if o.get('component_geometry_role')=='robe_sleeve')
        depsgraph=bpy.context.evaluated_depsgraph_get()
        return bpy.data.meshes.new_from_object(target.evaluated_get(depsgraph),depsgraph=depsgraph)
    finally:
        for obj in copies.values():
            mesh=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if mesh.users==0:
                bpy.data.meshes.remove(mesh)
        bpy.data.collections.remove(staging)


def apply_union(target, boolean):
    """Blender may report a cancelled Boolean without raising a Python error."""
    name=boolean.name
    result=bpy.ops.object.modifier_apply(modifier=name)
    if 'FINISHED' not in result or target.modifiers.get(name) is not None:
        raise RuntimeError('Blender could not apply the Manifold row union; no STL was exported')


def run(job_path):
    started=time.perf_counter()
    if bpy.app.version != (5,1,2):
        raise RuntimeError('Blender 5.1.2 is required')
    job=json.loads(Path(job_path).read_text())
    if any(not a['cached'] for a in job['assets'].values()):
        from fdm_sculpt.atelier_heightfield_blender import heightfield
        from fdm_sculpt.regiment_blender import ElfBuilder
        ElfBuilder.heightfield=heightfield
        compile_missing(job)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=.001
    sources=bpy.data.collections.new('SOURCE_PRIMITIVES')
    operands=bpy.data.collections.new('BOOLEAN_OPERANDS')
    exports=bpy.data.collections.new('EVALUATED_EXPORT')
    for collection in (sources,operands,exports):
        scene.collection.children.link(collection)
    sources.hide_viewport=sources.hide_render=True
    loaded={}
    sleeves={}
    for ref,asset in job['assets'].items():
        record=asset['manifest']
        with bpy.data.libraries.load(str(Path(asset['directory'])/'part.blend'),link=True) as (_,data):
            data.collections=[record['source_collection'],record['visual_collection']]
        loaded[ref]=data.collections
        if 'robe_sleeve' in asset['definition']['output_roles']:
            sleeves[ref]=export_sleeve(data.collections[0])
    target=None
    order=[]
    for placement in job['assembly']['placements']:
        source,visual=loaded[placement['part']]
        mount=Matrix(placement['mount'])
        original_source=bpy.data.objects.new('source/'+placement['instance_id'],None)
        original_source.instance_type='COLLECTION'
        original_source.instance_collection=source
        original_source.matrix_world=mount
        sources.objects.link(original_source)
        for original in sorted(visual.objects,key=lambda o:o.name):
            if original.type!='MESH':
                continue
            mesh=sleeves[placement['part']] if original.get('component_geometry_role')=='robe_sleeve' else original.data
            obj=bpy.data.objects.new(placement['instance_id']+'/'+original.name,mesh)
            # Cached collections are not linked into this scene. Their world
            # matrices may still be identity; matrix_basis is the saved local
            # transform used by the visual viewer and the atelier composer.
            obj.matrix_world=mount@original.matrix_basis
            obj['placement_json']=json.dumps(placement,sort_keys=True)
            order.append(obj.name)
            if target is None:
                target=obj
                target.data=original.data.copy()
                exports.objects.link(target)
            else:
                operands.objects.link(obj)
    if target is None:
        raise RuntimeError('The row contains no mesh objects')
    bpy.context.view_layer.objects.active=target
    target.select_set(True)
    boolean=target.modifiers.new('Row union — Manifold','BOOLEAN')
    boolean.operation='UNION'
    boolean.solver='MANIFOLD'
    boolean.operand_type='COLLECTION'
    boolean.collection=operands
    print('MANIFOLD_UNION',len(order),'mesh objects',flush=True)
    union_started=time.perf_counter()
    apply_union(target,boolean)
    union_seconds=time.perf_counter()-union_started
    print('MANIFOLD_UNION_FINISHED',round(union_seconds,3),'seconds',flush=True)
    target.name='Row — unchecked Blender union'
    target['solver']='MANIFOLD'
    target['validation_performed']=False
    target['union_order_json']=json.dumps(order)
    target['seed']=job['seed']
    operands.hide_viewport=operands.hide_render=True
    scene['assembly_json']=json.dumps(job['assembly'],sort_keys=True)
    scene['seed']=job['seed']
    scene['digitally_validated']=False
    scene['export_mode']='unchecked-blender-manifold-union'
    output=Path(job['output'])
    bpy.ops.wm.stl_export(filepath=str(output/'row.stl'),export_selected_objects=True,
                          apply_modifiers=False,global_scale=1.0,use_scene_unit=False,
                          ascii_format=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'row.blend'))
    result=dict(solver='MANIFOLD',operation='UNION',validation_performed=False,digitally_validated=False,
                input_objects=len(order),union_seconds=round(union_seconds,3),
                elapsed_seconds=round(time.perf_counter()-started,3),
                label='Unchecked Blender output',union_order=order,
                export_sleeve_solver='MANIFOLD',export_sleeve_parts=sorted(sleeves))
    (output/'union-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('BLENDER_STL_EXPORTED',flush=True)


if __name__=='__main__':
    run(sys.argv[sys.argv.index('--')+1])
