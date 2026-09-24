"""Apply the accepted print design to all current army recipes, without Blender."""
import json,sys,os
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.core import ComponentDefinition,component_digest
from fdm_sculpt.components.parts import validate_part,resolve_assembly
from fdm_sculpt.components.elves_v2 import identity
from fdm_sculpt.components.accepted_army import part_map,upgrade,fitted_spear_joins
from fdm_sculpt.components.bolder_faces import revised_parts,apply as apply_faces
from fdm_sculpt.components.recessed_face import revised_part as recessed_part,apply as apply_recessed
from fdm_sculpt.components.raised_insignia import revised_part as raised_insignia
from fdm_sculpt.components.larger_crest import revised_part as larger_crest
from fdm_sculpt.components.taller_helmets import revised_parts as taller_helmets
from fdm_sculpt.components.fierce_insignia import revised_part as fierce_insignia
from fdm_sculpt.components.pointed_helmets import revised_parts as pointed_helmets, apply as apply_pointed
from fdm_sculpt.components.leaning_spears import apply as apply_spear_lean

class Definitions(dict):
    def __missing__(self,ref):
        part=validate_part(ComponentDefinition.from_dict(json.loads(
            (ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text())))
        self[ref]=part;return part

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def generate():
    sources=json.loads((ROOT/'specs/accepted-army-sources.json').read_text())['sources']
    definitions=Definitions()
    insignia=raised_insignia(definitions)
    fierce=fierce_insignia(definitions)
    crest=larger_crest(definitions)
    definitions[insignia.reference]=insignia
    definitions[fierce.reference]=fierce
    definitions[crest.reference]=crest
    mapping,parts=part_map(sources,definitions);definitions.update(parts)
    output={};turns={}
    for name,source in sources.items():
        spec,angles=upgrade(source,mapping,definitions)
        extra=fitted_spear_joins(spec,definitions);parts.update(extra);definitions.update(extra)
        output[name]=spec;turns[name]=angles
    # Reuse the locked, printed shapes for the default five-pose composition.
    reviewed=json.loads((ROOT/'specs/baselines/spearmen-printed-20260923.json').read_text())
    reviewed['assembly_id']=sources['specs/elf-modular-visual.json']['assembly_id']
    reviewed['label']='Locked spearmen - five glue-in figures'
    for p in reviewed['placements']:p['instance_id']=p['instance_id'].replace('row-','elf-')
    output['specs/elf-modular-visual.json']=reviewed
    # Unit rows share the accepted recess pitch; individual gallery bases retain
    # their original transforms and the matching 4 x 5 x 1 source footing.
    for name in ('specs/elf-unit-archers.json','specs/elf-unit-center-standard.json'):
        spec=output[name];placements=[p for p in spec['placements'] if '/' in p['instance_id']]
        groups=sorted({p['instance_id'].split('/')[0] for p in placements})
        for i,group in enumerate(groups):
            origin=(i-2)*4;destination=(i-2)*7.6/1.3
            for p in placements:
                if p['instance_id'].startswith(group+'/'):
                    p['mount'][0][3]+=destination-origin;p['mount'][2][3]+=.8/1.3
            for slot,ref,z in [('footing','aurelian.glue-footing@1',.8/1.3),
                               ('terrain','aurelian.terrain-soil-gallery@5',1+.8/1.3)]:
                m=identity();m[0][3]=destination;m[2][3]=z
                part=definitions[ref];placements.append(dict(instance_id=group+'/'+slot,part=ref,definition_sha256=part.sha256,mount=m))
        ref='aurelian.glue-tray-five-walled@2'
        placements.insert(0,dict(instance_id='tray',part=ref,definition_sha256=definitions[ref].sha256,mount=identity()))
        spec['placements']=placements
    faces=revised_parts(definitions)
    definitions.update({p.reference:p for p in faces.values()})
    taller=taller_helmets(definitions)
    definitions.update({p.reference:p for p in taller.values()})
    pointed=pointed_helmets(definitions)
    definitions.update({p.reference:p for p in pointed.values()})
    recessed=recessed_part(definitions)
    definitions[recessed.reference]=recessed
    parts.pop(insignia.reference,None)
    parts[fierce.reference]=fierce
    parts[crest.reference]=crest
    for spec in output.values():apply_faces(spec,faces)
    for spec in output.values():apply_recessed(spec,recessed)
    for spec in output.values():
        for placement in spec['placements']:
            for old,part in taller.items():
                if placement['part']==old:
                    placement.update(part=part.reference,definition_sha256=part.sha256)
    for spec in output.values():
        for placement in spec['placements']:
            if placement['part'] == 'aurelian.readable-insignia-trial@4':
                placement.update(part=fierce.reference,definition_sha256=fierce.sha256)
    from fdm_sculpt.components.accepted_army import yaw
    from fdm_sculpt.components.elves_v2 import multiply
    import math
    for spec in output.values():
        groups={}
        for placement in spec['placements']:
            if '/' in placement['instance_id']:
                group,slot=placement['instance_id'].split('/',1);groups.setdefault(group,{})[slot]=placement
        for group,slots in groups.items():
            if group not in ('elf-02','02-watching-left') or 'shield' not in slots:continue
            shield=slots['shield'];current=math.degrees(math.atan2(shield['mount'][1][0],shield['mount'][0][0]))
            if abs(18-current)<1e-9:continue
            turn=yaw([r[3] for r in shield['mount'][:3]],18-current)
            for slot in ('shield','shield-insignia'):
                if slot in slots:slots[slot]['mount']=multiply(turn,slots[slot]['mount'])
    for spec in output.values():apply_pointed(spec,pointed)
    for spec in output.values():apply_spear_lean(spec,definitions)
    output['specs/elf-modular-visual.json']['label']='Locked spearmen - five glue-in figures'
    for name,spec in output.items():
        resolve_assembly(spec,definitions)
        if name.startswith('specs/models/'):
            key=Path(name).stem
            model_library=dict(schema_version=1,assembly_id='accepted-'+key,placements=[])
            for p in spec['placements']:
                q=deepcopy(p);q['instance_id']=key+'/'+q['instance_id'].split('/',1)[1]
                model_library['placements'].append(q)
            model_path=ROOT/'specs/accepted-army-models'/f'{key}.json'
            write(model_path,model_library)
            relative=os.path.relpath(model_path,(ROOT/name).parent).replace('\\','/')
            write(ROOT/name,dict(schema_version=1,model_id=spec['assembly_id'],source=dict(assembly=relative,figure=key,origin_mm=[0,0,0])))
        else:write(ROOT/name,spec)
    for ref,part in {**parts,**{p.reference:p for p in faces.values()},recessed.reference:recessed,fierce.reference:fierce,crest.reference:crest,**{p.reference:p for p in taller.values()},**{p.reference:p for p in pointed.values()}}.items():
        path=ROOT/'fdm_sculpt/components/parts'/f'{ref}.json'
        if path.exists():assert json.loads(path.read_text())==part.to_dict(),f'Use a new revision: {ref}'
        else:write(path,part.to_dict())
    write(ROOT/'tests/fixtures/bolder-faces-golden.json',{p.reference:p.sha256 for p in faces.values()})
    write(ROOT/'tests/fixtures/recessed-face-golden.json',{recessed.reference:recessed.sha256})
    write(ROOT/'tests/fixtures/raised-insignia-golden.json',{insignia.reference:insignia.sha256})
    write(ROOT/'tests/fixtures/fierce-insignia-golden.json',{fierce.reference:fierce.sha256})
    write(ROOT/'tests/fixtures/larger-crest-golden.json',{crest.reference:crest.sha256})
    golden_path=ROOT/'tests/fixtures/pointed-helmets-golden.json'
    pointed_golden=json.loads(golden_path.read_text()) if golden_path.exists() else {}
    pointed_golden.update({p.reference:p.sha256 for p in pointed.values()})
    write(golden_path,pointed_golden)
    write(ROOT/'tests/fixtures/taller-helmets-golden.json',{ref:p.sha256 for ref,p in taller.items()})
    write(ROOT/'tests/fixtures/accepted-army-golden.json',{ref:p.sha256 for ref,p in sorted(parts.items())})
    write(ROOT/'specs/accepted-army-index.json',dict(schema_version=1,seed=1001,export_scale=1.3,status='visual-only',
        source='accepted-army-sources.json',accepted_reference='spearmen-locked-baseline.json',
        spearmen_baseline='spearmen-locked-baseline.json',
        assemblies=[n for n in output if not n.startswith('specs/models/')],
        models=[n for n in output if n.startswith('specs/models/')],
        replacements=mapping,new_parts=sorted(parts),shield_turns=turns,
        face_update={ref:p.reference for ref,p in faces.items()},
        pointed_helmet_update={ref:p.reference for ref,p in pointed.items()},
        notes='Broader bodies, full arms and grips, readable faces/mail, raised emblems and broad leaf weapons. Physical acceptance applies only to the original five-pose infantry test.'))
    print(f'Updated {len(output)} assemblies/models; {len(parts)} new reusable parts.',flush=True)
    return definitions,output,parts

if __name__=='__main__':generate()
