import json
from pathlib import Path

import pytest

from fdm_sculpt.components.upper_spear_trial import build
from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT=Path(__file__).resolve().parents[1]


def test_upper_spear_trial_is_pinned_and_preserves_poses_and_lower_shafts():
    definitions=catalog()
    figures=[json.loads((ROOT/f'specs/experiments/glue-figure-{i}-trial.json').read_text()) for i in range(1,6)]
    parts,specs=build(figures,definitions)
    assert {p.reference:p.sha256 for p in parts}==json.loads((ROOT/'tests/fixtures/upper-spear-fill-golden.json').read_text())
    for part in parts:assert definitions[part.reference].to_dict()==part.to_dict()
    for spec in specs:
        resolve_assembly(spec,definitions)
        assert json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())==spec
    params=parts[0].to_dict()['parameters']
    original=definitions[params['experiment']['source']].to_dict()['parameters']
    assert params['atoms'][0]==original['atoms'][0]
    assert params['landmarks']==original['landmarks']
    upper=next(a for a in params['atoms'] if a['role']=='upper_shaft')
    assert 2*upper['radius']*1.3==pytest.approx(2.08)
    for source,trial in zip(figures,specs[:5]):
        for a,b in zip(source['placements'],trial['placements'][:-1]):
            assert a['instance_id']==b['instance_id'] and a['mount']==b['mount']
            if not a['instance_id'].endswith('/spear'):assert a==b
        assert trial['placements'][-1]['instance_id'].endswith('/helmet-spear-fill')
    assert specs[5]['placements']==specs[0]['placements'][:-1]
    for part in parts[1:]:
        params=part.to_dict()['parameters']
        assert params['landmarks']['shoulder_root'][2]<params['landmarks']['helmet_contact'][2]
        assert params['experiment']['minimum_top_thickness_mm']>=.75
        assert params['operations']==[dict(target='shoulder_fill',operand='rounded_fill_top',operation='UNION',solver='EXACT')]
