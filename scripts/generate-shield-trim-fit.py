"""Pin recessed mail trim without changing shield poses or lower joins."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.elves_v2 import multiply, translation
from fdm_sculpt.components.shield_trim_fit import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    manifest = json.loads((ROOT / 'specs/shield-trim-fit-sources.json').read_text())
    parts = revised_parts(catalog(), manifest, seed)
    for part in parts:
        write_definition(part, ROOT / 'fdm_sculpt/components/parts')
    golden = ROOT / 'tests/fixtures' / f"shield-trim-fit-v{manifest['version']}-golden.json"
    payload = json.dumps({p.reference: p.sha256 for p in parts}, indent=2) + '\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    path = ROOT / 'specs/elf-modular-visual.json'
    data = json.loads(path.read_text())
    placements = {p['instance_id']: p for p in data['placements']}
    for pose, part in zip(manifest['poses'], parts):
        placements[pose['trim']['instance_id']].update(
            part=part.reference, definition_sha256=part.sha256)
    path.write_text(json.dumps(data, indent=2) + '\n')
    # Models that remove the shield retain their complete, reviewed edging.
    for relative in ('elf-standard-bearer.json', 'elf-swordmaster.json',
                     'spearmen/10-hawk-sergeant.json'):
        path = ROOT / 'specs/models' / relative
        data = json.loads(path.read_text())
        pose = next(p for p in manifest['poses'] if p['figure'] == data['source']['figure'])
        trim = dict(pose['trim'], instance_id='skirt-trim')
        trim['mount'] = multiply(translation([-v for v in data['source']['origin_mm']]),
                                 trim['mount'])
        data['parts'] = [p for p in data['parts'] if p['instance_id'] != 'skirt-trim'] + [trim]
        path.write_text(json.dumps(data, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, required=True)
    generate(parser.parse_args().seed)
