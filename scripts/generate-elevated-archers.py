"""Generate three rear-rank models and pinned arm recipes without Blender."""
import json
from copy import deepcopy
from pathlib import Path
from fdm_sculpt.army import load_model
from fdm_sculpt.components.archer_elevation import elevated_arm,elevation_transform
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.terrain import write_definition

ROOT=Path(__file__).resolve().parent.parent

def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')

def main():
    d=catalog();golden={}
    base={p['instance_id']:p for p in load_model(ROOT/'specs/models/archers/01-aiming-forward.json',d)['placements']}
    gallery_path=ROOT/'specs/elf-archer-variants.json'
    gallery=json.loads(gallery_path.read_text())
    index_path=ROOT/'specs/archer-variants-index.json';index=json.loads(index_path.read_text())
    index['variants']=[v for v in index['variants'] if v['number']<=10]
    gallery['models']=gallery['models'][:10]
    gallery['placements']=[p for p in gallery['placements'] if int(p['instance_id'].split('-')[1])<=10]
    rear=dict(schema_version=1,assembly_id='aurelian-archer-rear-ranks',label='Rear-rank archers: 20, 30, 40 degrees',placements=[],models=[])
    for number,degrees in enumerate((20,30,40),11):
        slug=f'{number:02d}-aiming-up-{degrees}'
        model=json.loads((ROOT/'specs/models/archers/01-aiming-forward.json').read_text())
        model['model_id']='aurelian-archer-'+slug
        model['transforms']={slot:elevation_transform(degrees,[.55,-.75,8]) for slot in ('bow','bow-ferrule','arrow')}
        model['transforms'].update({slot:elevation_transform(degrees*.6,[.002243391,-.136002621,7.35]) for slot in ('head','helmet','crest')})
        for slot in ('bow-arm','draw-arm'):
            arm=elevated_arm(d[base[slot]['part']],degrees=degrees,seed=1001)
            write_definition(arm,ROOT/'fdm_sculpt/components/parts');golden[arm.reference]=arm.sha256
            model['parts'].append(dict(base[slot],part=arm.reference,definition_sha256=arm.sha256))
        write(ROOT/f'specs/models/archers/{slug}.json',model)
        index['variants'].append(dict(number=number,label=f'Aiming upward {degrees} degrees',model=f'models/archers/{slug}.json',state='nocked',yaw_degrees=0,bow_roll_degrees=0,elevation_degrees=degrees))
        x=(number-12)*6
        for target,y in ((gallery,16),(rear,0)):
            for template in gallery['placements'][:2]:
                p=deepcopy(template);p['instance_id']=p['instance_id'].replace('01',str(number));p['mount'][0][3]=x;p['mount'][1][3]=y
                target['placements'].append(p)
            placement=deepcopy(gallery['models'][0]);placement.update(instance_id='variant-'+slug,model=f'models/archers/{slug}.json')
            placement['mount'][0][3]=x;placement['mount'][1][3]=y
            target['models'].append(placement)
    gallery['label']='Archer variants (13)'
    write(gallery_path,gallery);write(index_path,index);write(ROOT/'specs/elf-archer-rear-ranks.json',rear)
    write(ROOT/'tests/fixtures/archer-elevation-v1-golden.json',golden)

if __name__=='__main__':main()
