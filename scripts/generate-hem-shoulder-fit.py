"""Pin the reviewed hem and shoulder fit corrections without recompiling poses."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.hem_shoulder_fit import revised_parts, center_shoulders
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    definitions = catalog()
    parts = revised_parts(definitions, seed)
    replacements = {}
    for part in parts:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
        definitions[part.reference] = part
        replacements[part.to_dict()['parameters']['fit_source']] = part
    golden = ROOT/'tests/fixtures/hem-shoulder-fit-golden.json'
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
    assembly = center_shoulders(assembly, definitions)
    path.write_text(json.dumps(assembly, indent=2)+'\n')
    print(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, required=True)
    generate(parser.parse_args().seed)
