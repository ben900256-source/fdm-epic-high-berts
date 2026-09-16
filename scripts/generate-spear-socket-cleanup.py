"""Pin the spear shaft cleanup while preserving historical studies."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.spear_socket_cleanup import revised_spear
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    part=revised_spear(catalog(),seed)
    write_definition(part,ROOT/'fdm_sculpt/components/parts')
    golden=ROOT/'tests/fixtures/spear-socket-cleanup-golden.json'
    payload=json.dumps({part.reference:part.sha256},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    path=ROOT/'specs/elf-modular-visual.json'
    data=json.loads(path.read_text())
    for placement in data['placements']:
        if placement['part']=='aurelian.spear@4':
            placement.update(part=part.reference,definition_sha256=part.sha256)
    path.write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
