import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.army import load_model,load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swordmaster_variants import POSES,posed_arm,rotation
from fdm_sculpt.components.elves_v2 import multiply

ROOT=Path(__file__).resolve().parent.parent

def test_ten_swordmaster_guards():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/swordmaster-variants-v1-golden.json').read_text())
    for _ in range(2):assert {p.reference:p.sha256 for n in range(1,11) for side in ('left','right') for p in [posed_arm(n,side,1001)]}==golden
    assert {ref:d[ref].sha256 for ref in golden}==golden
    index=json.loads((ROOT/'specs/swordmaster-variants-index.json').read_text())['variants'];assert len(index)==10
    base={p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-swordmaster.json',d)['placements']}
    for entry,pose in zip(index,POSES):
        m={p['instance_id']:p for p in load_model(ROOT/'specs'/entry['model'],d)['placements']}
        def anchor(slot,name):
            v=d[m[slot]['part']].to_dict()['parameters']['landmarks'][name];matrix=m[slot]['mount']
            return [sum(matrix[i][j]*v[j] for j in range(3))+matrix[i][3] for i in range(3)]
        for side,grip in [('left','lower_grip'),('right','upper_grip')]:assert anchor(side+'-arm','grip')==pytest.approx(anchor('greatsword',grip))
        assert abs(pose[4])<=4
        for slot in base:
            if slot in ('left-arm','right-arm','greatsword'):continue
            assert m[slot]['part']==base[slot]['part']
            assert m[slot]['mount']==multiply(rotation('z',pose[4]),base[slot]['mount'])
    gallery=load_assembly(ROOT/'specs/elf-swordmaster-variants.json',d)
    assert len(gallery['placements'])==190

@pytest.mark.integration
def test_saved_swordmaster_gallery():
    if not os.environ.get('SWORDMASTER_VARIANTS_PROOF'):pytest.skip('set SWORDMASTER_VARIANTS_PROOF for saved gallery')
    output=ROOT/'out/elf-swordmaster-variants-v1'
    proof=json.loads((output/'saved-provenance.json').read_text())
    assert proof['passes'] and all(proof['checks'].values())
    review=json.loads((output/'visual-review.json').read_text())
    assert not review['digitally_validated']
    assert len(review['compiled_parts'])==18 and all('-arm-pose-' in ref for ref in review['compiled_parts'])
