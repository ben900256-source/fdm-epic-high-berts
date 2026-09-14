import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swordmaster_helmets import officer_helmet,officer_waist

ROOT=Path(__file__).resolve().parent.parent


def test_officer_regalia_goldens():
    d=catalog()
    for name,recipe in [('helmet',lambda:officer_helmet(d['aurelian.helmet@5'],1001)),('waist',lambda:officer_waist(1001))]:
        golden=json.loads((ROOT/f'tests/fixtures/swordmaster-sergeant-{name}-v1-golden.json').read_text())
        for _ in range(2):
            p=recipe();assert p.sha256==d[p.reference].sha256==golden[p.reference]

def test_swordmaster_sergeant_reuses_upright_guard():
    d=catalog()
    base={p['instance_id']:p for p in load_model(ROOT/'specs/models/swordmasters/10-upright-guard.json',d)['placements']}
    officer={p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-swordmaster-sergeant.json',d)['placements']}
    assert officer.keys()==base.keys()
    for slot in base:
        for i in range(4):assert officer[slot]['mount'][i]==pytest.approx(base[slot]['mount'][i],abs=1e-8)
        assert officer[slot]['part']==({'helmet':'aurelian.swordmaster-sergeant-helmet@2','waist-armour':'aurelian.swordmaster-sergeant-waist@3'}.get(slot,base[slot]['part']))
    assert officer['helmet']['mount']==officer['head']['mount']==officer['helmet-plume']['mount']

@pytest.mark.integration
def test_saved_swordmaster_sergeant():
    if not os.environ.get('SWORDMASTER_SERGEANT_PROOF'):pytest.skip('set SWORDMASTER_SERGEANT_PROOF for saved scene')
    output=ROOT/'out/elf-swordmaster-sergeant-fitted-waist-v3'
    proof=json.loads((output/'saved-provenance.json').read_text())
    review=json.loads((output/'visual-review.json').read_text())
    assert proof['passes'] and all(proof['checks'].values())
    assert set(review['compiled_parts']) <= {'aurelian.swordmaster-sergeant-helmet@2','aurelian.swordmaster-sergeant-waist@3'}
    assert not review['digitally_validated']
