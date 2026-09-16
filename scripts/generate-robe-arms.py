"""Generate pinned cloth arms and replace separate spearman sleeve overlays."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.robe_arms import revised_parts, fitted_bow_shoulders
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    manifest = json.loads((ROOT/'specs/robe-arm-sources.json').read_text())
    parts = revised_parts(catalog(),manifest,seed)
    for part in parts:
        write_definition(part,ROOT/'fdm_sculpt/components/parts')
    golden = ROOT/'tests/fixtures/robe-arms-golden.json'
    payload = json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n'
    if golden.exists() and golden.read_text()!=payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    replacements = {p.to_dict()['parameters']['robe_source']:p for p in parts}
    fitted=fitted_bow_shoulders(catalog(),seed)
    fitted_golden=ROOT/'tests/fixtures/robe-arm-shoulders-golden.json'
    fitted_payload=json.dumps({p.reference:p.sha256 for p in fitted},indent=2)+'\n'
    if fitted_golden.exists() and fitted_golden.read_text()!=fitted_payload:
        raise ValueError('preserve reviewed shoulder golden hashes')
    for part in fitted:
        write_definition(part,ROOT/'fdm_sculpt/components/parts')
        params=part.to_dict()['parameters']
        replacements[params['robe_source']]=part
        replacements[params['shoulder_fit_source']]=part
    fitted_golden.write_text(fitted_payload)
    master = ROOT/'specs/elf-modular-visual.json'
    for path in [master,*sorted((ROOT/'specs/models').rglob('*.json'))]:
        data = json.loads(path.read_text())
        before = json.dumps(data)
        if path == master:
            data['placements'] = [p for p in data['placements']
                                  if not p['instance_id'].endswith(('/left-tunic','/right-tunic'))]
        if path.name == 'elf-archer.json':
            data['remove'] = [s for s in data['remove'] if s not in ('left-tunic','right-tunic')]
        for placement in data.get('placements',data.get('parts',[])):
            if placement['part'] in replacements:
                part = replacements[placement['part']]
                placement.update(part=part.reference,definition_sha256=part.sha256)
        if json.dumps(data)!=before:
            path.write_text(json.dumps(data,indent=2)+'\n')
    print(f'Pinned {len(parts)} posed cloth-arm revisions')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,required=True)
    generate(parser.parse_args().seed)
