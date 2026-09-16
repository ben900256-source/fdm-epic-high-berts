import json
from pathlib import Path

from fdm_sculpt.army import load_model
from fdm_sculpt.components.cloth_robes import revised_parts, fitted_sleeves, folded_capes, front_folded_sleeves
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.workshop import models

ROOT=Path(__file__).resolve().parents[1]


def test_cloth_recipes_preserve_ground_clearance_and_remove_armor_caps():
    definitions=catalog()
    golden=json.loads((ROOT/'tests/fixtures/cloth-robes-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in revised_parts(definitions,1001)}==golden
    assert {r:definitions[r].sha256 for r in golden}==golden
    fitted=json.loads((ROOT/'tests/fixtures/fitted-cloth-sleeves-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in fitted_sleeves(definitions,1001)}==fitted
    assert {r:definitions[r].sha256 for r in fitted}==fitted
    fronts=json.loads((ROOT/'tests/fixtures/front-folded-sleeves-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in front_folded_sleeves(definitions,1001)}==fronts
    assert {r:definitions[r].sha256 for r in fronts}==fronts
    capes=json.loads((ROOT/'tests/fixtures/folded-capes-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in folded_capes(definitions,1001)}==capes
    for ref,sha in capes.items():
        assert definitions[ref].sha256==sha
        p=definitions[ref].to_dict()['parameters']
        source=definitions[p['robe_source']].to_dict()['parameters']
        assert p['atoms'][:len(source['atoms'])]==source['atoms']
    for side in ('left','right'):
        p=definitions[f'aurelian.{side}-tunic@4'].to_dict()['parameters']
        assert all('pauldron' not in a['role'] and 'hem' not in a['role'] for a in p['atoms'])
        assert p['atoms'][0]['dimensions'][0]<.9
    before=definitions['aurelian.skirt@8'].to_dict()['parameters']
    after=definitions['aurelian.skirt@9'].to_dict()['parameters']
    assert next(a for a in before['atoms'] if a['role']=='hem_ground_transition')==next(a for a in after['atoms'] if a['role']=='hem_ground_transition')
    assert not any('skirt_link' in a['role'] for a in after['atoms'])
    assert after['landmarks']==before['landmarks']
    assert len([a for a in after['atoms'] if a['role'].startswith('robe_fold_')])==14


def test_family_clothing_pins_and_swordmaster_preservation():
    definitions=catalog()
    counts=dict(spearmen=0,swordsmen=0,archers=0,swordmasters=0)
    for model in models():
        slots={p['instance_id']:p['part'] for p in load_model(model['path'],definitions)['placements']}
        family=model['family']
        counts[family]+=1
        if family in ('spearmen','swordsmen'):
            assert 'left-tunic' not in slots and 'right-tunic' not in slots
            for slot,ref in slots.items():
                if slot.endswith('-arm'):
                    assert 'cloth_pose' in definitions[ref].to_dict()['parameters']
            assert slots['skirt']=='aurelian.skirt@8'
            assert slots['cape'].endswith('@5')
        elif family=='archers':
            assert slots['tunic']=='aurelian.archer-tunic@5'
        else:
            assert slots['left-tunic']=='aurelian.left-tunic@2'
            assert slots['right-tunic']=='aurelian.right-tunic@3'
            assert slots['skirt']=='aurelian.skirt@8'
            assert slots['cape']=='aurelian.cape-c@4'
    assert counts==dict(spearmen=9,swordsmen=3,archers=14,swordmasters=11)
