"""Generate pinned grip rotations and apply their model-specific placements."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.hand_alignment import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    manifest=json.loads((ROOT/'specs/hand-alignment-sources.json').read_text())
    parts=revised_parts(catalog(),manifest,seed)
    for part in parts:write_definition(part,ROOT/'fdm_sculpt/components/parts')
    definitions={p.reference:p for p in parts}
    golden=ROOT/'tests/fixtures/hand-alignment-golden.json'
    payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    for filename,edits in manifest['files'].items():
        path=ROOT/filename; data=json.loads(path.read_text())
        key='placements' if 'placements' in data else 'parts'
        for edit in edits:
            replacement=dict(instance_id=edit['instance_id'],part=edit['part'],
                definition_sha256=definitions[edit['part']].sha256,mount=edit['mount'])
            old=next((p for p in data[key] if p['instance_id']==edit['instance_id']),None)
            if old is None:data[key].append(replacement)
            else:old.update(replacement)
        path.write_text(json.dumps(data,indent=2)+'\n')
    print(f'Pinned {len(parts)} grip revisions')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
