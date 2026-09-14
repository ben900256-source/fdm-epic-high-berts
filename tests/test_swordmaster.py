import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.army import load_model,load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swordmasters import swordmaster_parts
from fdm_sculpt.components.swordmaster_armour import armour_parts,rounded_crown_braid,metal_pauldrons,helmet_plume,flowing_hair_plume,custom_hair_plume

ROOT=Path(__file__).resolve().parent.parent

def test_swordmaster_goldens_and_two_handed_grip():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/swordmaster-v1-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in swordmaster_parts(1001)}==golden
    assert {ref:d[ref].sha256 for ref in golden}==golden
    m={p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-swordmaster.json',d)['placements']}
    def anchor(slot,name):
        v=d[m[slot]['part']].to_dict()['parameters']['landmarks'][name];matrix=m[slot]['mount']
        return [sum(matrix[i][j]*v[j] for j in range(3))+matrix[i][3] for i in range(3)]
    for side,grip in [('left','lower_grip'),('right','upper_grip')]:
        assert anchor(side+'-arm','grip')==pytest.approx(anchor('greatsword',grip))
    assert not any('shield' in slot or slot=='spear' for slot in m)
    assert m['head']['part']=='aurelian.head@12' and m['helmet']['part']=='aurelian.helmet@5'
    assert m['skirt-trim']['mount']==m['skirt']['mount']
    source=load_assembly(ROOT/'specs/elf-modular-visual.json',d)
    old={p['instance_id'].split('/')[1]:p for p in source['placements'] if p['instance_id'].startswith('elf-03/')}
    assembled=load_assembly(ROOT/'specs/elf-swordmaster.json',d)
    for p in assembled['placements']:
        slot=p['instance_id'].split('/')[-1]
        if slot in ('left-leg','right-leg','skirt','cape','torso'):
            assert p['mount']==old[slot]['mount'] and p['part']==old[slot]['part']

@pytest.mark.integration
def test_saved_swordmaster_provenance():
    if not os.environ.get('SWORDMASTER_PROOF'):pytest.skip('set SWORDMASTER_PROOF for saved visual review')
    output=ROOT/'out/elf-swordmaster-v1'
    proof=json.loads((output/'saved-provenance.json').read_text())
    assert proof['passes'] and all(proof['checks'].values())
    review=json.loads((output/'visual-review.json').read_text())
    assert not review['digitally_validated']
    assert set(review['compiled_parts'])==set(json.loads((ROOT/'tests/fixtures/swordmaster-v1-golden.json').read_text()))


def test_heavy_armour_recipes_and_mounts():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/swordmaster-armour-v1-golden.json').read_text())
    for _ in range(2):assert {p.reference:p.sha256 for p in armour_parts(d,1001)}==golden
    assert {ref:d[ref].sha256 for ref in golden}==golden
    braid_golden=json.loads((ROOT/'tests/fixtures/swordmaster-braid-v2-golden.json').read_text())
    for _ in range(2):
        braid=rounded_crown_braid(1001)
        assert braid.sha256==d[braid.reference].sha256==braid_golden[braid.reference]
    m={p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-swordmaster.json',d)['placements']}
    assert 'waist-wrap' not in m and 'crest' not in m
    assert m['helmet-plume']['mount']==m['helmet']['mount']
    assert 'crown-braid' not in m
    assert m['pauldrons']['mount']==m['waist-armour']['mount']==m['torso']['mount']
    assert m['mail']['part']=='aurelian.swordmaster-cuirass@1'


@pytest.mark.integration
def test_saved_armour_provenance():
    if not os.environ.get('SWORDMASTER_PROOF'):pytest.skip('set SWORDMASTER_PROOF for saved visual review')
    output=ROOT/'out/elf-swordmaster-custom-hair-v3'
    proof=json.loads((output/'saved-provenance.json').read_text())
    assert proof['passes'] and all(proof['checks'].values())
    before=json.loads((ROOT/'out/elf-swordmaster-plume-metal-v1/assembly-job.json').read_text())
    after=json.loads((output/'assembly-job.json').read_text())
    for ref in before['assets'].keys() & after['assets'].keys():assert before['assets'][ref]['key']==after['assets'][ref]['key']
    def without_hair(job):return [p for p in job['assembly']['placements'] if not p['instance_id'].endswith('/helmet-plume')]
    assert without_hair(before)==without_hair(after)


def test_plume_and_metal_goldens():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/swordmaster-plume-metal-golden.json').read_text())
    for _ in range(2):assert {p.reference:p.sha256 for p in [metal_pauldrons(1001),helmet_plume(1001)]}==golden
    assert {ref:d[ref].sha256 for ref in golden}==golden
    plume=helmet_plume(1001).to_dict()['parameters']
    assert plume['landmarks']['drape'][2]<0
    assert plume['landmarks']['drape'][1]<=1.1


def test_flowing_hair_golden_and_recessed_detail():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/swordmaster-hair-v2-golden.json').read_text())
    for _ in range(2):
        hair=flowing_hair_plume(1001)
        assert hair.sha256==d[hair.reference].sha256==golden[hair.reference]
    params=hair.to_dict()['parameters']
    assert all(o['operation']=='DIFFERENCE' for o in params['operations'][2:])
    assert len([a for a in params['atoms'] if a['primitive']=='sphere'])==3


def test_custom_hair_recipe():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/swordmaster-hair-v3-golden.json').read_text())
    for _ in range(2):
        hair=custom_hair_plume(1001)
        assert hair.sha256==d[hair.reference].sha256==golden[hair.reference]
    p=hair.to_dict()['parameters']
    assert p['landmarks']['drape'][0]>.4 and p['landmarks']['drape'][2]<-.5
    assert p['landmarks']['crown']==[0,.1,1.88]
