"""Write immutable shorter capes and repin the current assembly."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.cape_hems import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    parts = revised_parts(catalog(), seed)
    replacements = {}
    for part in parts:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
        replacements[part.to_dict()['parameters']['hem_revision']['source']] = part
        replacements[part.component_id+'@3'] = part
    golden = ROOT/'tests/fixtures/cape-hems-v4-golden.json'
    payload = json.dumps({p.reference:p.sha256 for p in parts}, indent=2)+'\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    path = ROOT/'specs/elf-modular-visual.json'
    assembly = json.loads(path.read_text())
    for placement in assembly['placements']:
        if placement['part'] in replacements:
            part = replacements[placement['part']]
            placement.update(part=part.reference, definition_sha256=part.sha256)
    path.write_text(json.dumps(assembly, indent=2)+'\n')
    print(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, required=True)
    generate(parser.parse_args().seed)
