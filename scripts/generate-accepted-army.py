"""Apply the accepted print design to all current army recipes, without Blender."""
import json,sys,os
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.core import ComponentDefinition,component_digest
from fdm_sculpt.components.parts import validate_part,resolve_assembly
from fdm_sculpt.components.elves_v2 import identity
from fdm_sculpt.components.accepted_army import part_map,upgrade,fitted_spear_joins

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
    definitions=Definitions();mapping,parts=part_map(sources,definitions);definitions.update(parts)
    output={};turns={}
    for name,source in sources.items():
        spec,angles=upgrade(source,mapping,definitions)
        extra=fitted_spear_joins(spec,definitions);parts.update(extra);definitions.update(extra)
        output[name]=spec;turns[name]=angles
    # Keep the five accepted poses intact in the default composition.
    reviewed=json.loads((ROOT/'specs/experiments/wider-shield-walled-row-trial.json').read_text())
    reviewed['assembly_id']=sources['specs/elf-modular-visual.json']['assembly_id']
    reviewed['label']='Accepted wider-shield infantry — visual-only'
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
    for ref,part in parts.items():
        path=ROOT/'fdm_sculpt/components/parts'/f'{ref}.json'
        if path.exists():assert json.loads(path.read_text())==part.to_dict(),f'Use a new revision: {ref}'
        else:write(path,part.to_dict())
    write(ROOT/'tests/fixtures/accepted-army-golden.json',{ref:p.sha256 for ref,p in sorted(parts.items())})
    write(ROOT/'specs/accepted-army-index.json',dict(schema_version=1,seed=1001,export_scale=1.3,status='visual-only',
        source='accepted-army-sources.json',accepted_reference='experiments/wider-shield-infantry-3-trial.json',
        assemblies=[n for n in output if not n.startswith('specs/models/')],
        models=[n for n in output if n.startswith('specs/models/')],
        replacements=mapping,new_parts=sorted(parts),shield_turns=turns,
        notes='Broader bodies, full arms and grips, readable faces/mail, raised emblems and broad leaf weapons. Physical acceptance applies only to the original five-pose infantry test.'))
    print(f'Updated {len(output)} assemblies/models; {len(parts)} new reusable parts.',flush=True)
    return definitions,output,parts

if __name__=='__main__':generate()
