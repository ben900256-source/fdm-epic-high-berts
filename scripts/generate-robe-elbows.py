"""Add elbow cloth texture while preserving the reviewed sleeve silhouette."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.robe_elbows import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    manifest=json.loads((ROOT/'specs/robe-elbow-sources.json').read_text())
    parts=revised_parts(catalog(),manifest,seed)
    golden=ROOT/'tests/fixtures/robe-elbows-golden.json'
    payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:
        raise ValueError('preserve reviewed golden hashes')
    for part in parts:write_definition(part,ROOT/'fdm_sculpt/components/parts')
    golden.write_text(payload)
    replacements={p.to_dict()['parameters']['elbow_texture_source']:p for p in parts}
    for path in [ROOT/'specs/elf-modular-visual.json',*sorted((ROOT/'specs/models').rglob('*.json'))]:
        data=json.loads(path.read_text()); changed=False
        for placement in data.get('placements',data.get('parts',[])):
            if placement['part'] in replacements:
                part=replacements[placement['part']]
                placement.update(part=part.reference,definition_sha256=part.sha256)
                changed=True
        if changed:path.write_text(json.dumps(data,indent=2)+'\n')
    print(f'Pinned {len(parts)} elbow-texture revisions')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
