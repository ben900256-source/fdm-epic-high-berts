import json
from pathlib import Path

import pytest

from fdm_sculpt.components.pointed_helmets import revised_parts
from test_accepted_army import Definitions

ROOT = Path(__file__).resolve().parents[1]


def test_pointed_revisions_keep_face_opening_and_original_tip_profile():
    definitions = Definitions()
    parts = revised_parts(definitions)
    expected = json.loads((ROOT/'tests/fixtures/pointed-helmets-golden.json').read_text())
    assert all(expected[p.reference] == p.sha256 for p in parts.values())
    assert all(definitions[ref].sha256 == value for ref,value in expected.items())
    for part in parts.values():
        assert definitions[part.reference].to_dict() == part.to_dict()
        p = part.to_dict()['parameters']
        if 'pointed_helmet' not in p:
            continue
        source = definitions[p['pointed_helmet']['source']].to_dict()['parameters']
        before = {a['role']:a for a in source['atoms']}
        after = {a['role']:a for a in p['atoms']}
        for role in before:
            if role not in ('helmet_crown', 'helmet_tapered_tip'):
                assert after[role] == before[role]
        tip = after['helmet_tapered_tip']
        crown = after['helmet_crown']
        join = tip['location'][2]-tip['depth']/2
        u = (join-crown['location'][2])/(crown['dimensions'][2]/2)
        assert tip['radius1'] == pytest.approx(crown['dimensions'][0]/2*(1-u*u)**.5)
        assert tip['radius2'] <= before['helmet_tapered_tip']['radius2']
        assert tip['location'][2]+tip['depth']/2 == pytest.approx(3.16)
        assert p['landmarks']['mount'] == source['landmarks']['mount']


def test_current_rows_and_models_use_fitted_crests_and_pointed_helmets():
    index = json.loads((ROOT/'specs/accepted-army-index.json').read_text())
    definitions = Definitions()
    paths = [ROOT/p for p in index['assemblies']]
    paths.extend((ROOT/'specs/accepted-army-models').glob('*.json'))
    used = set()
    for path in paths:
        spec = json.loads(path.read_text(encoding='utf-8'))
        for placement in spec['placements']:
            ref = placement['part']
            if ref.startswith('aurelian.crest@'):
                assert ref == 'aurelian.crest@7', path
            if ref in index['pointed_helmet_update']:
                pytest.fail(f'{path} still uses superseded part {ref}')
            used.add(ref)
            assert placement['definition_sha256'] == definitions[ref].sha256
    assert set(index['pointed_helmet_update'].values()) <= used
