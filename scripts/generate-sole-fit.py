"""Pin sole front-edge trims across the current infantry models."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.sole_fit import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    manifest=json.loads((ROOT/'specs/sole-fit-sources.json').read_text())
    parts=revised_parts(catalog(),manifest,seed)
    for part in parts:write_definition(part,ROOT/'fdm_sculpt/components/parts')
    golden=ROOT/'tests/fixtures/sole-fit-golden.json'
    payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    replacements={p.to_dict()['parameters']['sole_fit']['source']:p for p in parts}
    for path in [ROOT/'specs/elf-modular-visual.json',*sorted((ROOT/'specs/models').rglob('*.json'))]:
        data=json.loads(path.read_text()); changed=False
        for placement in data.get('placements',data.get('parts',[])):
            if placement['part'] in replacements:
                part=replacements[placement['part']]
                placement.update(part=part.reference,definition_sha256=part.sha256); changed=True
        if changed:path.write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
