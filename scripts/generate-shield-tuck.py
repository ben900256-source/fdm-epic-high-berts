"""Pin inward shield poses and their concealed hem joins."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_tuck import revised_parts, tucked_mount, recessed_join_mount
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    manifest = json.loads((ROOT/'specs/shield-tuck-sources.json').read_text())
    parts = revised_parts(catalog(), manifest, seed)
    for part in parts:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
    golden = ROOT/'tests/fixtures'/f"shield-tuck-v{manifest['version']}-golden.json"
    payload = json.dumps({p.reference:p.sha256 for p in parts}, indent=2)+'\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    path = ROOT/'specs/elf-modular-visual.json'
    data = json.loads(path.read_text())
    placements = {p['instance_id']:p for p in data['placements']}
    for pose,part in zip(manifest['poses'],parts):
        for name in ('shield','insignia'):
            placements[pose[name]['instance_id']]['mount'] = tucked_mount(pose)
        placements[pose['connector']['instance_id']].update(part=part.reference, definition_sha256=part.sha256,
                                                          mount=recessed_join_mount(pose))
    path.write_text(json.dumps(data, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, required=True)
    generate(parser.parse_args().seed)
