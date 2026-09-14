"""Write the swordmaster's reusable pieces and visual assembly; no Blender."""
import json
from pathlib import Path
from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swordmasters import swordmaster_parts,ROTATION,UPPER_GRIP
from fdm_sculpt.components.elves_v2 import multiply,translation
from fdm_sculpt.components.terrain import write_definition

ROOT=Path(__file__).resolve().parent.parent

def main():
    definitions=catalog();parts=swordmaster_parts(1001)
    for d in parts:write_definition(d,ROOT/'fdm_sculpt/components/parts');definitions[d.reference]=d
    def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n')
    write('tests/fixtures/swordmaster-v1-golden.json',{d.reference:d.sha256 for d in parts})
    source=load_assembly(ROOT/'specs/elf-modular-visual.json',definitions)
    slots={p['instance_id'].split('/')[1]:dict(p,mount=multiply(translation([0,0,-1]),p['mount'])) for p in source['placements'] if p['instance_id'].startswith('elf-03/')}
    def placement(slot,ref,mount):return dict(instance_id=slot,part=ref,definition_sha256=definitions[ref].sha256,mount=mount)
    model=dict(schema_version=1,model_id='aurelian-swordmaster',source=dict(assembly='../elf-modular-visual.json',figure='elf-03',origin_mm=[0,0,1]),
        remove=['spear','equipment-joins','right-arm','left-arm','shield','shield-insignia','shield-torso-connector','shield-lower-connector'],
        parts=[placement(side+'-arm','aurelian.swordmaster-'+side+'-arm@1',slots['torso']['mount']) for side in ('left','right')])
    model['parts'].append(placement('greatsword','aurelian.swordmaster-greatsword@1',multiply(slots['torso']['mount'],multiply(translation(UPPER_GRIP),ROTATION))))
    # Face forward while the existing stance and cape keep their subtle lean.
    head=slots['head']['mount'];m=[[1,0,0,head[0][3]],[0,1,0,head[1][3]],[0,0,1,head[2][3]],[0,0,0,1]]
    model['parts'].extend(placement(slot,slots[slot]['part'],m) for slot in ('head','helmet','crest'))
    write('specs/models/elf-swordmaster.json',model)
    write('specs/elf-swordmaster.json',dict(schema_version=1,assembly_id='aurelian-swordmaster',label='Bertmaster — two-handed greatsword',
        placements=[placement('base','aurelian.base-body-4x5@1',translation([0,0,0])),placement('base-terrain','aurelian.terrain-soil-gallery@4',translation([0,0,2]))],
        models=[dict(instance_id='swordmaster-01',model='models/elf-swordmaster.json',mount=translation([0,0,1]))]))

if __name__=='__main__':main()
