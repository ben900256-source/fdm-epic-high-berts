import json
from pathlib import Path

import pytest

from fdm_sculpt.components.open_arm_infantry import build
from fdm_sculpt.components.parts import catalog, resolve_assembly
from fdm_sculpt.components.elves_v2 import point

ROOT=Path(__file__).resolve().parents[1]


def test_open_arms_keep_shoulders_feet_and_shift_grips_with_equipment():
    definitions=catalog()
    figures=[json.loads((ROOT/f'specs/experiments/readable-infantry-{i}-trial.json').read_text()) for i in range(1,6)]
    parts,specs=build(figures,definitions)
    assert {p.reference:p.sha256 for p in parts}==json.loads((ROOT/'tests/fixtures/open-arm-infantry-golden.json').read_text())
    for part in parts:assert definitions[part.reference].to_dict()==part.to_dict()
    for spec in specs:
        resolve_assembly(spec,definitions)
        assert spec==json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())
    for before,after in zip(figures,specs[:5]):
        old={p['instance_id'].split('/')[-1]:p for p in before['placements']}
        new={p['instance_id'].split('/')[-1]:p for p in after['placements']}
        for slot in ('footing','terrain','left-leg','right-leg','torso','helmet','crest'):
            assert old[slot]==new[slot]
        for side,sign,equipment in [('left',-1,'shield'),('right',1,'spear')]:
            a,b=old[side+'-arm'],new[side+'-arm']
            pa,pb=(definitions[p['part']].to_dict()['parameters'] for p in (a,b))
            assert pb['cloth_pose']['shoulder']==pa['cloth_pose']['shoulder']
            assert pb['arm_trial']['sleeve_diameter_factor']==1.25
            for key in (side+'_palm',side+'_grouped_fingers',side+'_cuff'):
                x,y=point(a['mount'],pa['landmarks'][key]),point(b['mount'],pb['landmarks'][key])
                assert [y[i]-x[i] for i in range(3)]==pytest.approx([sign*.5,0,0],abs=1e-7)
            assert new[equipment]['part']==old[equipment]['part']
            for row in range(3):
                assert new[equipment]['mount'][row][:3]==old[equipment]['mount'][row][:3]
                assert new[equipment]['mount'][row][3]-old[equipment]['mount'][row][3]==pytest.approx(sign*.5 if row==0 else 0)
            original_hands={a['role']:a for a in pa['atoms'] if any(t in a['role'] for t in ('palm','fingers','thumb','knuckle'))}
            for atom in pb['atoms']:
                if atom['role'] in original_hands:
                    assert atom.get('dimensions')==original_hands[atom['role']].get('dimensions')
