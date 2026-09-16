"""Write immutable flush-nape parts and update current spearman pins."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.helmet_nape import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    parts = revised_parts(catalog(), seed)
    for part in parts:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
    golden = ROOT/'tests/fixtures/helmet-nape-v7-golden.json'
    payload = json.dumps({p.reference:p.sha256 for p in parts}, indent=2)+'\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    replacements = {'aurelian.helmet@5':parts[0], 'aurelian.helmet@6':parts[0], 'aurelian.torso@3':parts[1]}
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
    parser.add_argument('--seed', required=True, type=int)
    generate(parser.parse_args().seed)
