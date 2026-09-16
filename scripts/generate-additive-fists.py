"""Replace clipped fist pins with uncut hands and rounded additive tapers."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.additive_fists import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    m=json.loads((ROOT/'specs/additive-fists-sources.json').read_text())
    parts=revised_parts(catalog(),m,seed)
    for p in parts:write_definition(p,ROOT/'fdm_sculpt/components/parts')
    golden=ROOT/'tests/fixtures/additive-fists-v1-golden.json'
    payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:raise ValueError('Preserve golden hashes')
    golden.write_text(payload)
    replacements={p.to_dict()['parameters']['additive_fist_fit']['source']:p for p in parts}
    for path in [ROOT/'specs/elf-modular-visual.json',*sorted((ROOT/'specs/models').rglob('*.json'))]:
        data=json.loads(path.read_text());changed=False
        for item in data.get('placements',data.get('parts',[])):
            if item['part'] in replacements:
                p=replacements[item['part']];item.update(part=p.reference,definition_sha256=p.sha256);changed=True
        if changed:path.write_text(json.dumps(data,indent=2)+'\n')
    print('Pinned',len(parts),'uncut hands with additive tapers')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seed',type=int,required=True)
    generate(p.parse_args().seed)
