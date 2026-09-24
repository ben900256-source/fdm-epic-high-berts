"""Update current infantry reviews, preserving local figure coordinates."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.low_bases import revised_parts, BASE_SOURCES
from fdm_sculpt.components.terrain import write_definition

LAYOUTS = ['elf-modular-visual',
           'elf-spearman-variants', 'elf-spearman-hawk-sergeant',
           'elf-archer', 'elf-archer-sergeant', 'elf-archer-variants',
           'elf-archer-rear-ranks', 'elf-unit-archers', 'elf-standard-bearer',
           'elf-swordmaster', 'elf-swordmaster-sergeant', 'elf-swordmaster-variants']


def generate(seed):
    replacements = revised_parts(catalog(), seed)
    for part in replacements.values():
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
    golden = ROOT/'tests/fixtures/low-bases-golden.json'
    payload = json.dumps({p.reference: p.sha256 for p in replacements.values()}, indent=2)+'\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('Preserve reviewed golden hashes')
    golden.write_text(payload)
    shifted = set()
    for name in LAYOUTS:
        path = ROOT/'specs'/f'{name}.json'
        data = json.loads(path.read_text())
        if not any(p['part'] in BASE_SOURCES for p in data.get('placements', [])):
            continue
        for p in data['placements']:
            source = p['part']
            if source not in BASE_SOURCES:
                p['mount'][2][3] -= 1
            if source in replacements:
                part = replacements[source]
                p.update(part=part.reference, definition_sha256=part.sha256)
        for model in data.get('models', []):
            model['mount'][2][3] -= 1
        path.write_text(json.dumps(data, indent=2)+'\n')
        shifted.add(path.resolve())
    for path in (ROOT/'specs').glob('*.json'):
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or 'base_assembly' not in data:
            continue
        if (path.parent/data['base_assembly']).resolve() not in shifted:
            continue
        for model in data.get('models', []):
            model['mount'][2][3] -= 1
        path.write_text(json.dumps(data, indent=2)+'\n')
        shifted.add(path.resolve())
    # Inherited parts keep their local pose; only assembly elevation changes.
    for path in (ROOT/'specs/models').rglob('*.json'):
        data = json.loads(path.read_text())
        source = data.get('source')
        if source and (path.parent/source['assembly']).resolve() in shifted:
            source.setdefault('origin_mm', [0, 0, 0])[2] -= 1
            path.write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(dict(parts=len(set(p.reference for p in replacements.values())),
                          shifted_layouts=len(shifted))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True, type=int)
    generate(parser.parse_args().seed)
