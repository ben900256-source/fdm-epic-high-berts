"""Prepare the original spearman with unchanged mail and sealed internal voids."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from fdm_sculpt import blender_backend as bb
from fdm_sculpt.atelier_blender import verify
from fdm_sculpt.modular_print_blender import fuse, ordered_fuse


def run(review, prepared_build, mail_cache, output):
    review, prepared_build, mail_cache, output = map(Path,(review,prepared_build,mail_cache,output))
    internal=output/'internal';internal.mkdir()
    job=json.loads((review/'assembly-job.json').read_text());job['output']=str(internal)
    verify(job)
    for ref,manifest in json.loads(bpy.context.scene['asset_manifest_json']).items():job['assets'][ref]['manifest']=manifest
    helper=job['assets']['aurelian.mail-internal-fill@1']['definition']['parameters']
    skirt_sha = next(p['definition_sha256'] for p in job['assembly']['placements'] if p['part']=='aurelian.skirt@3')
    assert helper['source_definition_sha256'] == skirt_sha
    previous_inputs = json.loads((prepared_build/'build-inputs.json').read_text())
    previous_review = Path(previous_inputs['review'])
    assert bb._sha256_file(previous_review/'assembly-job.json') == previous_inputs['assembly_job_sha256']
    previous = json.loads((previous_review/'assembly-job.json').read_text())
    assert [p for p in previous['assembly']['placements'] if '/' not in p['instance_id']] == [p for p in job['assembly']['placements'] if '/' not in p['instance_id']]
    placements=[p for p in job['assembly']['placements'] if p['instance_id'].startswith('elf-01/')]
    body_placements=[p for p in placements if p['part'] not in ('aurelian.skirt@3','aurelian.mail-internal-fill@1','aurelian.spearman-join-fill@1')]
    source=bpy.data.collections.new('MANUFACTURING_OPERANDS');bpy.context.scene.collection.children.link(source)
    bpy.context.scene['manufacturing_output_directory']=str(internal)
    with bpy.data.libraries.load(str((prepared_build/'internal/prepared-parts.blend').resolve()),link=False) as (_,data):
        data.objects=[p['instance_id']+'.001' for p in body_placements]
    body=[]
    for p,obj in zip(body_placements,data.objects):
        if p['part'] == 'aurelian.equipment-joins@3':
            # Materialize only the newly revised brace; all other parts reuse checked geometry.
            bpy.data.objects.remove(obj, do_unlink=True)
            instance = bpy.data.objects[p['instance_id']]
            original, = [o for o in instance.instance_collection.objects if o.type == 'MESH']
            obj = bpy.data.objects.new(p['instance_id']+'.001', original.data.copy())
            obj.data.transform(Matrix(p['mount']) @ original.matrix_basis)
            obj['placement_json'] = json.dumps(p, sort_keys=True)
        else:
            assert json.loads(obj['placement_json'])==p,p['instance_id']
        source.objects.link(obj);body.append(obj)
    print('FUSING_BODY_WITHOUT_MAIL',len(body),flush=True)
    bare=fuse('body-without-mail',body,source,native_tessellation=False,resolve_self=False,numerical_weld_mm=.00001)
    bare_metrics = bb._object_metrics(bare)
    assert bare_metrics['artifact_preflight']['passes'] and bb._self_intersection_count(bare) == 0
    bpy.ops.wm.save_as_mainfile(filepath=str(internal/'body-without-mail.blend'))
    with bpy.data.libraries.load(str(mail_cache.resolve()),link=False) as (_,data):data.objects=['original-mail-internal-fill']
    mail=data.objects[0];source.objects.link(mail)
    metrics=bb._object_metrics(mail)
    assert metrics['artifact_preflight']['passes'] and bb._self_intersection_count(mail)==0
    skirt=next(p for p in placements if p['part']=='aurelian.skirt@3')
    mail.data=mail.data.copy();mail.data.transform(Matrix(skirt['mount'])@mail.matrix_world);mail.matrix_world=Matrix.Identity(4)
    print('JOINING_UNCHANGED_ORIGINAL_MAIL',flush=True)
    joined=fuse('original-spearman-with-sealed-voids',[bare,mail],source,
                native_tessellation=False,resolve_self=True,numerical_weld_mm=.00001)
    fill_placement=next(p for p in placements if p['part']=='aurelian.spearman-join-fill@1')
    fill_instance=bpy.data.objects[fill_placement['instance_id']]
    fills=[]
    for original in sorted(fill_instance.instance_collection.objects,key=lambda o:o.name):
        obj=bpy.data.objects.new(original.name+'-manufacturing',original.data.copy())
        obj.data.transform(Matrix(fill_placement['mount']) @ original.matrix_basis)
        source.objects.link(obj);fills.append(obj)
    figure=ordered_fuse('checked-original-spearman',[joined]+fills,source,small_closure=True)
    with bpy.data.libraries.load(str((prepared_build/'internal/union-failure.blend').resolve()),link=False) as (_,data):data.objects=['fused-base']
    base=data.objects[0];source.objects.link(base)
    assert bb._object_metrics(base)['artifact_preflight']['passes'] and bb._self_intersection_count(base)==0
    (internal/'assembly-job.json').write_text(json.dumps(job,indent=2))
    file=internal/'checked-parts.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(file))
    bpy.ops.file.make_paths_relative();bpy.ops.file.pack_all();bpy.ops.file.pack_libraries()
    bpy.ops.wm.save_as_mainfile(filepath=str(file))
    record=dict(scene='internal/checked-parts.blend',scene_sha256=bb._sha256_file(file),
                base_object=base.name,figure_object=figure.name,seed=job['seed'],
                original_mail_reference='aurelian.skirt@3',internal_fill_reference='aurelian.mail-internal-fill@1',
                join_fill_reference='aurelian.spearman-join-fill@1',
                figure_metrics=bb._object_metrics(figure),label='checked geometry cache; not a digitally validated print')
    (output/'figure-cache.json').write_text(json.dumps(record,indent=2))
    print('ORIGINAL_FIGURE_CACHE_COMPLETE',flush=True)


if __name__=='__main__':run(*sys.argv[sys.argv.index('--')+1:])
