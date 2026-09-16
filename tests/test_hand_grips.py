import json
from pathlib import Path

import pytest

from fdm_sculpt.army import load_model
from fdm_sculpt.components.hand_grips import align_hand
from fdm_sculpt.components.parts import catalog, inverse_rigid

ROOT = Path(__file__).resolve().parent.parent


def vector(m, v):
    return [sum(m[i][j]*v[j] for j in range(3)) for i in range(3)]


def test_horn_hand_follows_local_tangent_and_retains_pose():
    definitions = catalog()
    model = {p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-archer-sergeant.json', definitions)['placements']}
    old = definitions['aurelian.archer-signal-horn-arm@1']
    new = definitions['aurelian.archer-signal-horn-arm@2']
    atoms = {a['role']:a for a in definitions[model['horn']['part']].to_dict()['parameters']['atoms']}
    tangent = [b-a for a,b in zip(atoms['organic_round_15']['location'],atoms['organic_round_17']['location'])]
    direction = vector(inverse_rigid(model['horn-arm']['mount']), vector(model['horn']['mount'], tangent))
    golden = json.loads((ROOT/'tests/fixtures/archer-horn-hand-v2-golden.json').read_text())
    for _ in range(2):
        assert align_hand(old, 2, direction).sha256 == new.sha256 == golden[new.reference]
    p = new.to_dict()['parameters']
    original = old.to_dict()['parameters']
    assert p['operations'] == original['operations']
    for name in ('shoulder', 'elbow', 'grip'):
        assert p['landmarks'][name] == original['landmarks'][name]
    for before, after in zip(original['atoms'], p['atoms']):
        if before['role'].endswith(('_palm','_fingers','_thumb')):
            frame = after['frame_mm']
            assert [frame[i][2] for i in range(3)] == pytest.approx(p['landmarks']['grip_axis'])
            assert {k:v for k,v in after.items() if k!='frame_mm'} == before
        else:
            assert after == before
