"""Pin the swordmaster's heavy armor and helmet braid without Blender."""
import json
from pathlib import Path
from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swordmaster_armour import armour_parts,rounded_crown_braid,metal_pauldrons,helmet_plume,flowing_hair_plume,custom_hair_plume,fitted_waist_armour,enlarged_fitted_waist
from fdm_sculpt.components.terrain import write_definition

ROOT=Path(__file__).resolve().parent.parent

def main():
    d=catalog();parts=armour_parts(d,1001)
    for part in parts:write_definition(part,ROOT/'fdm_sculpt/components/parts');d[part.reference]=part
    braid=rounded_crown_braid(1001);write_definition(braid,ROOT/'fdm_sculpt/components/parts');d[braid.reference]=braid
    revised=[metal_pauldrons(1001),helmet_plume(1001)]
    for p in revised:write_definition(p,ROOT/'fdm_sculpt/components/parts');d[p.reference]=p
    hair=flowing_hair_plume(1001);write_definition(hair,ROOT/'fdm_sculpt/components/parts');d[hair.reference]=hair
    custom=custom_hair_plume(1001);write_definition(custom,ROOT/'fdm_sculpt/components/parts');d[custom.reference]=custom
    fitted=enlarged_fitted_waist(d['aurelian.swordmaster-waist-armour@1']);write_definition(fitted,ROOT/'fdm_sculpt/components/parts');d[fitted.reference]=fitted
    path=ROOT/'specs/models/elf-swordmaster.json';data=json.loads(path.read_text())
    for p in data['parts']:
        if p['part'] in {a.reference for a in parts}:p['definition_sha256']=d[p['part']].sha256
    path.write_text(json.dumps(data,indent=2)+'\n')
    model={p['instance_id']:p for p in load_model(path,d)['placements']}
    for slot in ('waist-wrap','crest'):
        if slot not in data['remove']:data['remove'].append(slot)
    replacements={'mail':'aurelian.swordmaster-cuirass@1','pauldrons':revised[0].reference,
        'waist-armour':fitted.reference,'helmet-plume':custom.reference}
    data['parts']=[p for p in data['parts'] if p['instance_id'] not in (*replacements,'crest','crown-braid')]
    for slot,ref in replacements.items():
        data['parts'].append(dict(instance_id=slot,part=ref,definition_sha256=d[ref].sha256,
            mount=model['head' if slot=='helmet-plume' else 'torso']['mount']))
    path.write_text(json.dumps(data,indent=2)+'\n')
    (ROOT/'tests/fixtures/swordmaster-armour-v1-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n')
    (ROOT/'tests/fixtures/swordmaster-braid-v2-golden.json').write_text(json.dumps({braid.reference:braid.sha256},indent=2)+'\n')
    (ROOT/'tests/fixtures/swordmaster-plume-metal-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in revised},indent=2)+'\n')
    (ROOT/'tests/fixtures/swordmaster-hair-v2-golden.json').write_text(json.dumps({hair.reference:hair.sha256},indent=2)+'\n')
    (ROOT/'tests/fixtures/swordmaster-hair-v3-golden.json').write_text(json.dumps({custom.reference:custom.sha256},indent=2)+'\n')
    (ROOT/'tests/fixtures/swordmaster-waist-v3-golden.json').write_text(json.dumps({fitted.reference:fitted.sha256},indent=2)+'\n')

if __name__=='__main__':main()
