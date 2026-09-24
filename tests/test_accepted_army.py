import json
from pathlib import Path

from fdm_sculpt.army import load_model
from fdm_sculpt.components.core import ComponentDefinition
from fdm_sculpt.components.parts import validate_part,resolve_assembly

ROOT=Path(__file__).resolve().parents[1]


class Definitions(dict):
    def __missing__(self,key):
        part=validate_part(ComponentDefinition.from_dict(json.loads(
            (ROOT/'fdm_sculpt/components/parts'/f'{key}.json').read_text())))
        self[key]=part
        return part


def test_every_current_figure_resolves_to_accepted_detail():
    index=json.loads((ROOT/'specs/accepted-army-index.json').read_text())
    defs=Definitions()
    assert len(index['models'])==49
    for name in index['assemblies']+index['models']:
        spec=load_model(ROOT/name,defs) if name in index['models'] else json.loads((ROOT/name).read_text())
        resolve_assembly(spec,defs)
        heads=[p for p in spec['placements'] if p['instance_id'].split('/')[-1]=='head']
        assert heads,name
        assert all(p['part']=='aurelian.readable-head-trial@5' for p in heads),name
        for p in spec['placements']:
            if p['instance_id'].split('/')[-1]=='shield-insignia':
                assert p['part']=='aurelian.readable-insignia-trial@6'
            if p['instance_id'].split('/')[-1]=='spear':
                assert p['part']=='aurelian.uniform-spear-140-trial@3'


def test_new_parts_are_pinned_and_equipment_grips_stay_fixed():
    defs=Definitions()
    hashes=json.loads((ROOT/'tests/fixtures/accepted-army-golden.json').read_text())
    for ref,expected in hashes.items():
        part=defs[ref];assert part.sha256==expected
        p=part.to_dict()['parameters'];meta=p.get('accepted_army')
        if not meta:continue
        original=defs[meta['source']]
        assert original.sha256==meta['source_sha256']
        if meta.get('grip_landmarks_unchanged'):
            old=original.to_dict()['parameters']['landmarks']
            for key,value in old.items():
                if key=='elbow' or key.endswith('_elbow'):continue
                assert p['landmarks'][key]==value,(ref,key)


def test_model_updates_preserve_special_equipment():
    sources=json.loads((ROOT/'specs/accepted-army-sources.json').read_text())['sources']
    defs=Definitions()
    slots={'bow','arrow','held-arrow','shortblade','greatsword','hunting-hawk','horn','reins','horse','banner'}
    for name,source in sources.items():
        if not name.startswith('specs/models/'):continue
        updated=load_model(ROOT/name,defs)
        after={p['instance_id']:p for p in updated['placements']}
        for p in source['placements']:
            slot=p['instance_id'].split('/')[-1]
            if slot in slots:
                assert after[slot]['part']==p['part'],(name,slot)
                assert after[slot]['mount']==p['mount'],(name,slot)
