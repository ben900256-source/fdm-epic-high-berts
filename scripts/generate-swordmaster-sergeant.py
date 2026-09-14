"""Compose a swordmaster officer from approved cached components."""
import json
from copy import deepcopy
from pathlib import Path
from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.elves_v2 import multiply,translation
from fdm_sculpt.components.swordmaster_helmets import officer_helmet,officer_waist,oval_gem_helmet
from fdm_sculpt.components.terrain import write_definition
from fdm_sculpt.components.swordmaster_armour import fitted_waist_armour,enlarged_fitted_waist

ROOT=Path(__file__).resolve().parent.parent

def main():
    d=catalog();gallery=json.loads((ROOT/'specs/elf-swordmaster-variants.json').read_text())
    instance=next(m for m in gallery['models'] if m['instance_id']=='variant-10-upright-guard')
    origin=[row[3] for row in instance['mount'][:3]]
    source=load_assembly(ROOT/'specs/elf-swordmaster-variants.json',d)
    helmet=next(p for p in source['placements'] if p['instance_id']==instance['instance_id']+'/helmet')
    definition=officer_helmet(d['aurelian.helmet@5'],1001)
    write_definition(definition,ROOT/'fdm_sculpt/components/parts');d[definition.reference]=definition
    ref=definition.reference
    (ROOT/'tests/fixtures/swordmaster-sergeant-helmet-v1-golden.json').write_text(json.dumps({ref:definition.sha256},indent=2)+'\n')
    definition=oval_gem_helmet(d['aurelian.helmet@5'],1001)
    write_definition(definition,ROOT/'fdm_sculpt/components/parts');d[definition.reference]=definition
    ref=definition.reference
    (ROOT/'tests/fixtures/swordmaster-sergeant-helmet-v2-golden.json').write_text(json.dumps({ref:definition.sha256},indent=2)+'\n')
    model=dict(schema_version=1,model_id='aurelian-swordmaster-sergeant',
        source=dict(assembly='../elf-swordmaster-variants.json',figure=instance['instance_id'],origin_mm=origin),
        parts=[dict(instance_id='helmet',part=ref,definition_sha256=d[ref].sha256,
            mount=multiply(translation([-v for v in origin]),helmet['mount']))])
    waist=officer_waist(1001);write_definition(waist,ROOT/'fdm_sculpt/components/parts')
    original_waist=waist
    waist=enlarged_fitted_waist(waist);write_definition(waist,ROOT/'fdm_sculpt/components/parts')
    original=next(p for p in source['placements'] if p['instance_id']==instance['instance_id']+'/waist-armour')
    model['parts'].append(dict(instance_id='waist-armour',part=waist.reference,definition_sha256=waist.sha256,
        mount=multiply(translation([-v for v in origin]),original['mount'])))
    (ROOT/'tests/fixtures/swordmaster-sergeant-waist-v1-golden.json').write_text(json.dumps({original_waist.reference:original_waist.sha256},indent=2)+'\n')
    (ROOT/'tests/fixtures/swordmaster-sergeant-waist-v3-golden.json').write_text(json.dumps({waist.reference:waist.sha256},indent=2)+'\n')
    (ROOT/'specs/models/elf-swordmaster-sergeant.json').write_text(json.dumps(model,indent=2)+'\n')
    review=deepcopy(json.loads((ROOT/'specs/elf-swordmaster.json').read_text()))
    review.update(assembly_id='aurelian-swordmaster-sergeant',label='Bertmaster sergeant')
    review['models']=[dict(instance_id='sergeant-01',model='models/elf-swordmaster-sergeant.json',mount=translation([0,0,1]))]
    (ROOT/'specs/elf-swordmaster-sergeant.json').write_text(json.dumps(review,indent=2)+'\n')

if __name__=='__main__':main()
