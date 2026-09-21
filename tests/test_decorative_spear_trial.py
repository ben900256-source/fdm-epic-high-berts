import json
from pathlib import Path

import pytest

from fdm_sculpt.components.decorative_spear_trial import build
from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('thicker', [False, True])
def test_decorative_blade_preserves_uniform_shaft_and_other_parts(thicker):
    definitions = catalog()
    source = 'decorative-spear' if thicker else 'uniform-spear'
    fixture = 'fuller-spear' if thicker else 'decorative-spear'
    figures = [json.loads((ROOT/f'specs/experiments/{source}-infantry-{i}-trial.json').read_text())
               for i in range(1, 6)]
    parts, specs = build(figures, definitions, thicker=thicker)
    assert {p.reference: p.sha256 for p in parts} == json.loads(
        (ROOT/f'tests/fixtures/{fixture}-golden.json').read_text())
    part = parts[0]
    assert definitions[part.reference].to_dict() == part.to_dict()
    old = definitions[f'aurelian.uniform-spear-140-trial@{2 if thicker else 1}'].to_dict()['parameters']
    new = part.to_dict()['parameters']
    for a, b in zip(old['atoms'], new['atoms']):
        if a['role'] not in ('spear_leaf_lower', 'spear_leaf_tip'):
            assert a == b
        elif thicker:
            assert b['scale'][1] == pytest.approx(a['scale'][1]*1.15)
            assert {k:v for k,v in a.items() if k != 'scale'} == {k:v for k,v in b.items() if k != 'scale'}
            assert a['scale'][::2] == b['scale'][::2]
    for name in ('mount', 'shaft_bottom', 'shaft_top', 'collar'):
        assert old['landmarks'][name] == new['landmarks'][name]
    for spec in specs:
        resolve_assembly(spec, definitions)
        assert spec == json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())
    for before, after in zip(figures, specs):
        for a, b in zip(before['placements'], after['placements']):
            assert a['mount'] == b['mount']
            if not a['instance_id'].endswith('/spear'):
                assert a == b
