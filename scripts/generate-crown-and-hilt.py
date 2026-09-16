"""Pin taller capped feather plumes and short-sword hilt revisions."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.crown_and_hilt import revised_parts
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    manifest=json.loads((ROOT/'specs/crown-and-hilt-sources.json').read_text())
    parts=revised_parts(catalog(),manifest,seed)
    for part in parts:write_definition(part,ROOT/'fdm_sculpt/components/parts')
    golden=ROOT/'tests/fixtures'/manifest.get('golden','crown-and-hilt-golden.json')
    payload=json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    replacements={}
    for part in parts:
        p=part.to_dict()['parameters'];fit=p.get('plume_height_fit',p.get('crown_height_fit',p.get('hilt_fit')))
        replacements[fit['source']]=part
        if 'hilt_fit' in p:
            for reference in manifest.get('previous_sword_refs',[]):replacements[reference]=part
    for path in [ROOT/'specs/elf-modular-visual.json',*sorted((ROOT/'specs/models').rglob('*.json'))]:
        data=json.loads(path.read_text());changed=False
        for p in data.get('placements',data.get('parts',[])):
            if p['part'] in replacements:
                part=replacements[p['part']]
                p.update(part=part.reference,definition_sha256=part.sha256);changed=True
        if changed:path.write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
