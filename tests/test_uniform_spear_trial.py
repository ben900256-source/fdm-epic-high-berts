import json
from pathlib import Path

from fdm_sculpt.components.uniform_spear_trial import build
from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT = Path(__file__).resolve().parents[1]


def test_uniform_shaft_and_fixed_poses_wrist_and_sleeves():
    definitions = catalog()
    figures = [json.loads((ROOT/f'specs/experiments/clear-face-infantry-{i}-trial.json').read_text())
               for i in range(1, 6)]
    parts, specs = build(figures, definitions)
    assert {p.reference: p.sha256 for p in parts} == json.loads(
        (ROOT/'tests/fixtures/uniform-spear-golden.json').read_text())
    for part in parts:
        assert definitions[part.reference].to_dict() == part.to_dict()
    shaft = parts[0].to_dict()['parameters']
    assert not any(a['role'] in ('upper_transition', 'upper_shaft') for a in shaft['atoms'])
    cylinder = next(a for a in shaft['atoms'] if a['role'] == 'spear')
    assert cylinder['radius'] == .70
    assert cylinder['depth'] == 13.35
    assert shaft['landmarks'] == definitions['aurelian.upper-spear-160-trial@1'].to_dict()['parameters']['landmarks']
    for spec in specs:
        resolve_assembly(spec, definitions)
        assert spec == json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())
    for before, after in zip(figures, specs):
        for old, new in zip(before['placements'], after['placements']):
            assert old['mount'] == new['mount']
            slot = old['instance_id'].split('/')[-1]
            if slot not in ('spear', 'right-arm'):
                assert old == new
            elif slot == 'right-arm':
                a, b = (definitions[p['part']].to_dict()['parameters'] for p in (old, new))
                assert a['cloth_pose'] == b['cloth_pose']
                assert a['landmarks'] == b['landmarks']
                for first, second in zip(a['atoms'], b['atoms']):
                    if not any(word in first['role'] for word in ('palm', 'fingers', 'thumb', 'knuckle')):
                        assert first == second
