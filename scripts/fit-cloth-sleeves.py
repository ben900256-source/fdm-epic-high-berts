"""Publish the second sleeve-shape revision without regenerating robes or poses."""
import json
from pathlib import Path
import sys
import argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.cloth_robes import fitted_sleeves, front_folded_sleeves
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    definitions=catalog()
    for recipe,fixture in ((fitted_sleeves,'fitted-cloth-sleeves'),(front_folded_sleeves,'front-folded-sleeves')):
        parts=recipe(definitions,seed)
        for part in parts:
            write_definition(part,ROOT/'fdm_sculpt/components/parts')
            definitions[part.reference]=part
        payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
        path=ROOT/f'tests/fixtures/{fixture}-golden.json'
        if path.exists() and path.read_text()!=payload:raise ValueError('preserve reviewed golden hashes')
        path.write_text(payload)
    path=ROOT/'specs/elf-modular-visual.json'
    assembly=json.loads(path.read_text())
    replacements={p.to_dict()['parameters']['robe_source']:p for p in parts}
    replacements.update({p.reference.replace('@6','@4'):p for p in parts})
    for placement in assembly['placements']:
        if placement['part'] in replacements:
            p=replacements[placement['part']]
            placement.update(part=p.reference,definition_sha256=p.sha256)
    path.write_text(json.dumps(assembly,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
