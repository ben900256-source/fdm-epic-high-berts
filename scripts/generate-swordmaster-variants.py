"""Generate ten pinned swordmaster models and a cached visual gallery."""
import json
from pathlib import Path
from copy import deepcopy
from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swordmaster_variants import POSES,posed_arm,sword_rotation,rotation
from fdm_sculpt.components.elves_v2 import multiply,translation
from fdm_sculpt.components.terrain import write_definition

ROOT=Path(__file__).resolve().parent.parent
def write(path,data):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n')

def main():
    d=catalog();golden={};base={p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-swordmaster.json',d)['placements']}
    solo=json.loads((ROOT/'specs/elf-swordmaster.json').read_text())
    gallery=dict(schema_version=1,assembly_id='aurelian-swordmaster-variants',label='Bertmaster variants (10)',placements=[],models=[])
    index=[]
    for number,pose in enumerate(POSES,1):
        slug=f'{number:02d}-{pose[0]}';parts=[]
        for side in ('left','right'):
            arm=posed_arm(number,side,1001)
            write_definition(arm,ROOT/'fdm_sculpt/components/parts');d[arm.reference]=arm;golden[arm.reference]=arm.sha256
            parts.append(dict(base[side+'-arm'],part=arm.reference,definition_sha256=arm.sha256))
        parts.append(dict(base['greatsword'],mount=multiply(base['torso']['mount'],multiply(translation(pose[3]),sword_rotation(pose)))))
        model=dict(schema_version=1,model_id='aurelian-swordmaster-'+pose[0],
            source=dict(assembly='../../elf-swordmaster.json',figure='swordmaster-01',origin_mm=[0,0,1]),
            parts=parts,transform=rotation('z',pose[4]))
        filename=f'models/swordmasters/{slug}.json';write('specs/'+filename,model)
        position=[(number-1)%5*10-20,(number-1)//5*15,0]
        for original in solo['placements']:
            p=deepcopy(original);p['instance_id']=f'{original["instance_id"]}-{number:02d}'
            p['mount']=multiply(translation(position),p['mount']);gallery['placements'].append(p)
        gallery['models'].append(dict(instance_id='variant-'+slug,model=filename,mount=translation([*position[:2],1])))
        index.append(dict(number=number,label=pose[0].replace('-',' ').title(),model=filename,yaw_degrees=pose[4]))
    write('specs/elf-swordmaster-variants.json',gallery)
    write('specs/swordmaster-variants-index.json',dict(seed=1001,variants=index))
    write('tests/fixtures/swordmaster-variants-v1-golden.json',golden)

if __name__=='__main__':main()
