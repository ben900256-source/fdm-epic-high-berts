import json
from pathlib import Path

from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_arm_cleanup import revised_part, lowered_shoulder

ROOT = Path(__file__).resolve().parents[1]


def test_cylinder_removed_and_surrounding_arm_preserved():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/shield-arm-cleanup-golden.json').read_text())
    for _ in range(2):
        part = revised_part(definitions, 1001)
        assert {part.reference:part.sha256} == golden
    assert definitions[part.reference].sha256 == part.sha256
    old = definitions['aurelian.left-arm@3'].to_dict()['parameters']
    new = part.to_dict()['parameters']
    assert new['atoms'] == [a for a in old['atoms'] if a['role'] != 'left_forearm']
    assert 'left_forearm' not in part.output_roles
    assert new['operations'] == old['operations']
    assert new['landmarks'] == {k:v for k,v in old['landmarks'].items() if k != 'left_forearm'}


def test_lowered_shoulder_preserves_the_rest_of_the_arm():
    definitions=catalog()
    golden=json.loads((ROOT/'tests/fixtures/lowered-shoulder-golden.json').read_text())
    for _ in range(2):
        part=lowered_shoulder(definitions,1001)
        assert {part.reference:part.sha256}==golden
    assert definitions[part.reference].sha256==part.sha256
    before=definitions['aurelian.left-arm@4'].to_dict()['parameters']
    after=part.to_dict()['parameters']
    for a,b in zip(before['atoms'],after['atoms']):
        if a['role']=='left_shoulder_slope':
            assert b['frame_mm'][2][3]==a['frame_mm'][2][3]-.20
            assert b['dimensions'][0]==a['dimensions'][0]*.85
        else:
            assert a==b
