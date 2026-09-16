"""Pin cloth robes and sleeves for spearmen and archers, preserving swordmasters."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.cloth_robes import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    definitions=catalog()
    # Freeze the three inherited armored garments before changing the source row.
    path=ROOT/'specs/models/elf-swordmaster.json'
    recipe=json.loads(path.read_text())
    old=load_model(path,definitions)
    overrides={p['instance_id'] for p in recipe['parts']}
    for p in old['placements']:
        if p['instance_id'] in ('left-tunic','right-tunic','skirt') and p['instance_id'] not in overrides:
            recipe['parts'].append(deepcopy(p))
    path.write_text(json.dumps(recipe,indent=2)+'\n')

    parts=revised_parts(definitions,seed)
    replacements={p.to_dict()['parameters']['robe_source']:p for p in parts}
    # The cloth-skirt prototype is preserved, but the accepted design keeps mail.
    replacements.pop('aurelian.skirt@8',None)
    for p in parts:
        write_definition(p,ROOT/'fdm_sculpt/components/parts')
    golden=ROOT/'tests/fixtures/cloth-robes-golden.json'
    payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    for filename,key in [('specs/elf-modular-visual.json','placements'),('specs/models/elf-archer.json','parts')]:
        path=ROOT/filename
        data=json.loads(path.read_text())
        for placement in data[key]:
            if placement['part'] in replacements:
                part=replacements[placement['part']]
                placement.update(part=part.reference,definition_sha256=part.sha256)
        path.write_text(json.dumps(data,indent=2)+'\n')
    print(payload)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
