import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swordmaster_armour import fitted_waist_armour,enlarged_fitted_waist
from fdm_sculpt.components.swordmaster_helmets import oval_gem_helmet

ROOT=Path(__file__).resolve().parent.parent

@pytest.mark.parametrize('revision',[2,3])
def test_fitted_waist_and_seated_gem_goldens(revision):
    d=catalog()
    for parent,fixture in [('aurelian.swordmaster-waist-armour@1','swordmaster-waist-v2-golden.json'),('aurelian.swordmaster-sergeant-waist@1','swordmaster-sergeant-waist-v2-golden.json')]:
        golden=json.loads((ROOT/'tests/fixtures'/fixture.replace('v2',f'v{revision}')).read_text())
        for _ in range(2):
            p=(fitted_waist_armour if revision==2 else enlarged_fitted_waist)(d[parent]);assert p.sha256==d[p.reference].sha256==golden[p.reference]
        atoms={a['role']:a for a in p.to_dict()['parameters']['atoms']}
        for side in (-1,1):
            a=atoms[f'tasset_{side}'];assert a['dimensions'][1]<.43
            assert abs(a['frame_mm'][0][1])>.5
            if revision==3:assert a['dimensions'][0]>1.2 and a['dimensions'][2]>2
        assert atoms['central_plate']==next(a for a in d[parent].to_dict()['parameters']['atoms'] if a['role']=='central_plate')
    golden=json.loads((ROOT/'tests/fixtures/swordmaster-sergeant-helmet-v2-golden.json').read_text())
    for _ in range(2):
        p=oval_gem_helmet(d['aurelian.helmet@5'],1001);assert p.sha256==d[p.reference].sha256==golden[p.reference]
    a={a['role']:a for a in p.to_dict()['parameters']['atoms']}
    assert a['oval_brow_gem']['primitive']=='sphere' and 'officer_brow_badge' not in a
    assert a['oval_brow_gem']['location'][2]-a['oval_brow_gem']['dimensions'][2]/2>.7

@pytest.mark.integration
def test_saved_fitted_waist_scenes():
    if not os.environ.get('FITTED_WAIST_PROOF'):pytest.skip('set FITTED_WAIST_PROOF for saved scenes')
    for name,previous in [('elf-swordmaster','custom-hair-v3'),('elf-swordmaster-variants','v1'),('elf-swordmaster-sergeant','regalia-v1')]:
        output=ROOT/f'out/{name}-fitted-waist-v3'
        proof=json.loads((output/'saved-provenance.json').read_text());assert proof['passes'] and all(proof['checks'].values())
        old=json.loads((ROOT/f'out/{name}-{previous}/assembly-job.json').read_text())
        new=json.loads((output/'assembly-job.json').read_text())
        for ref in old['assets'].keys() & new['assets'].keys():assert old['assets'][ref]['key']==new['assets'][ref]['key']
        def fixed(job):return [p for p in job['assembly']['placements'] if p['instance_id'].split('/')[-1] not in ('waist-armour','helmet')]
        assert fixed(old)==fixed(new)
