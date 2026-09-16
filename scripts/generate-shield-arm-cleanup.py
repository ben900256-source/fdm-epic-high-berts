"""Save the cylinder-free shield arm and update its current assembly pin."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_arm_cleanup import revised_part
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    part = revised_part(catalog(), seed)
    write_definition(part, ROOT/'fdm_sculpt/components/parts')
    golden = ROOT/'tests/fixtures/shield-arm-cleanup-golden.json'
    payload = json.dumps({part.reference:part.sha256}, indent=2)+'\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    path = ROOT/'specs/elf-modular-visual.json'
    assembly = json.loads(path.read_text())
    for placement in assembly['placements']:
        if placement['part'] == 'aurelian.left-arm@3':
            placement.update(part=part.reference, definition_sha256=part.sha256)
    path.write_text(json.dumps(assembly, indent=2)+'\n')
    print(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, required=True)
    generate(parser.parse_args().seed)
