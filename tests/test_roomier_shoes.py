import json
import os
from pathlib import Path
import pytest

from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.roomier_shoes import revised_parts, SOLE_WIDTH, SOLE_LENGTH

ROOT=Path(__file__).resolve().parents[1]


def test_shoes_repeat_resolve_and_preserve_heel_and_leg_geometry():
    definitions=catalog()
    golden=json.loads((ROOT/'tests/fixtures/roomier-shoes-v5-golden.json').read_text())
    for _ in range(2):
        parts=revised_parts(definitions,1001)
        assert {p.reference:p.sha256 for p in parts}==golden
    assert {ref:definitions[ref].sha256 for ref in golden}==golden
    for part in parts:
        p=part.to_dict()['parameters'];old=definitions[p['shoe_fit']['source']].to_dict()['parameters']
        before={a['role']:a for a in old['atoms']};after={a['role']:a for a in p['atoms']}
        side='left' if 'left-leg' in part.component_id else 'right'
        for role,a in before.items():
            b=after[role]
            if role in (side+'_sole',side+'_toe'):
                assert b['frame_mm']==a['frame_mm']
                assert b['location'][1]+b['dimensions'][1]/2==pytest.approx(a['location'][1]+a['dimensions'][1]/2)
                assert b['location'][2]-b['dimensions'][2]/2==pytest.approx(a['location'][2]-a['dimensions'][2]/2)
                assert b['dimensions'][0]>a['dimensions'][0] and b['dimensions'][1]>a['dimensions'][1]
            else:
                assert a==b
        assert after[side+'_sole']['dimensions'][:2]==[SOLE_WIDTH,SOLE_LENGTH]
        assert p['operations'][:len(old['operations'])]==old['operations']
        assert all(op['solver']=='EXACT' for op in p['operations'])


@pytest.mark.integration
def test_saved_shoe_fit_and_provenance():
    output=os.environ.get('ROOMIER_SHOES_REVIEW')
    if not output:
        pytest.skip('set ROOMIER_SHOES_REVIEW to the assembled shoe study')
    output=Path(output)
    proof=json.loads((output/'saved-provenance.json').read_text())
    fit=json.loads((output/'shoe-trim-fit.json').read_text())
    assert proof['passes'] and proof['checks']['visual_only'] and proof['checks']['hidden_sources']
    assert fit['passes'] and len(fit['checks'])==10
    for item in fit['checks']:
        assert proof['checks'][item['instance']]
        assert item['crossing_faces']==0 and item['sampled_clearance_mm']>.025
