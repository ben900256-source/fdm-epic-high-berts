"""Pin ten forward spear variants and their permanent terrain supports."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.elves_v2 import translation
from fdm_sculpt.components.terrain import write_definition
from fdm_sculpt.components.forward_spearmen import generate_parts


def write(path,data):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(data,indent=2)+'\n'
    if path.exists() and path.read_text()!=payload:raise ValueError('Preserve pinned recipe: '+str(path))
    path.write_text(payload)


def generate(seed):
    manifest=json.loads((ROOT/'specs/forward-spearmen-sources.json').read_text())
    definitions=catalog();parts,poses=generate_parts(definitions,manifest,seed)
    for part in parts:
        write_definition(part,ROOT/'fdm_sculpt/components/parts');definitions[part.reference]=part
    write(Path('tests/fixtures')/manifest.get('golden','forward-spearmen-v1-golden.json'),{p.reference:p.sha256 for p in parts})
    source=dict(placements=manifest['model_parts'])
    def placement(slot,ref,mount):
        return dict(instance_id=slot,part=ref,definition_sha256=definitions[ref].sha256,mount=mount)
    gallery=dict(schema_version=1,assembly_id='aurelian-forward-spearmen',
                 label='Forward spear variants (10)',placements=[],models=[])
    index=[]
    for pose in poses:
        n=pose['number'];angle=pose['elevation'];name=f'{n+10:02d}-forward-spear-{angle:02d}-degrees'
        slots={p['instance_id']:dict(p) for p in source['placements'] if p['instance_id']!='equipment-joins'}
        slots['right-arm']=placement('right-arm',pose['arm'],manifest['arm_mount'])
        slots['spear']=placement('spear',manifest['spear'],pose['spear_mount'])
        slots['spear-terrain-rests']=placement('spear-terrain-rests',pose['support'],translation([0,0,0]))
        slots['forward-base-extension']=placement('forward-base-extension','aurelian.forward-base-extension@1',translation([0,-8.9,0]))
        slots['forward-base-terrain']=placement('forward-base-terrain','aurelian.forward-base-terrain@1',translation([0,-8.9,1]))
        for item in slots.values():
            if item['part'] in manifest.get('review_replacements',{}):
                ref=manifest['review_replacements'][item['part']]
                item.update(part=ref,definition_sha256=definitions[ref].sha256)
        model=dict(schema_version=1,model_id='aurelian-'+name,
            source=dict(assembly='../../elf-modular-visual.json',figure='elf-01',origin_mm=[-8,0,0]),
            remove=['equipment-joins'],parts=list(slots.values()),
            forward_spear=dict(elevation_degrees=angle,permanent_terrain_supports=True,base_footprint_mm=[4,18]))
        write(Path('specs/models/spearmen')/(name+'.json'),model)
        offset=[(n-1)%5*8-16,(n-1)//5*25,0]
        gallery['models'].append(dict(instance_id=f'forward-{n:02d}',model=f'models/spearmen/{name}.json',mount=translation(offset)))
        gallery['placements'].extend([
            placement(f'base-{n:02d}','aurelian.base-body-4x5-plain@1',translation(offset)),
            placement(f'base-{n:02d}-terrain','aurelian.terrain-soil-gallery@5',translation([offset[0],offset[1],1]))])
        index.append(dict(model=f'models/spearmen/{name}.json',**dict(pose,arm=slots['right-arm']['part'])))
    write(Path('specs/elf-forward-spearmen.json'),gallery)
    write(Path('specs/forward-spearmen-index.json'),dict(seed=seed,variants=index))
    print('Pinned',len(poses),'forward spearmen and',len(parts),'parts')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seed',type=int,required=True)
    generate(p.parse_args().seed)
