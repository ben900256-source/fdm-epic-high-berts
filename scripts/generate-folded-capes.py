"""Keep spearman mail skirts and add cloth folds to the capes."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.cloth_robes import folded_capes
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    definitions=catalog()
    path=ROOT/'specs/models/elf-swordmaster.json'
    data=json.loads(path.read_text())
    if not any(p['instance_id']=='cape' for p in data['parts']):
        cape=next(p for p in load_model(path,definitions)['placements'] if p['instance_id']=='cape')
        data['parts'].append(deepcopy(cape))
        path.write_text(json.dumps(data,indent=2)+'\n')
    parts=folded_capes(definitions,seed)
    for p in parts:write_definition(p,ROOT/'fdm_sculpt/components/parts')
    path=ROOT/'tests/fixtures/folded-capes-golden.json'
    payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if path.exists() and path.read_text()!=payload:raise ValueError('preserve reviewed golden hashes')
    path.write_text(payload)
    replacements={p.to_dict()['parameters']['robe_source']:p for p in parts}
    replacements['aurelian.skirt@9']=definitions['aurelian.skirt@8']
    path=ROOT/'specs/elf-modular-visual.json'
    data=json.loads(path.read_text())
    for placement in data['placements']:
        if placement['part'] in replacements:
            p=replacements[placement['part']]
            placement.update(part=p.reference,definition_sha256=p.sha256)
    path.write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
