import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.dragon_princes import cavalry_parts,open_face_barding
from fdm_sculpt.components.dragon_prince_reference import reference_parts,connected_head_parts,scale_helmets,upright_helmets,swept_visor,larger_shield,great_shield,flexed_steed,scalp_barding,routed_reins,gem_shield,scaled_shield,dense_scaled_shield,supported_lance_seal,flush_reins,angular_pauldrons,fitted_reins,bridle_fitted_reins,tapestry_lance,heroic_steed

ROOT=Path(__file__).resolve().parent.parent


def test_heroic_steed_keeps_joint_bends_and_ground_contacts():
    d=catalog();old=d['aurelian.dragon-prince-horse@4'].to_dict()['parameters']
    new=heroic_steed(1001).to_dict()['parameters']
    assert old['landmarks']==new['landmarks']
    a={p['role']:p for p in old['atoms']};b={p['role']:p for p in new['atoms']}
    for role,p in a.items():
        if p['primitive']=='between':
            assert p['start']==b[role]['start'] and p['end']==b[role]['end']
            assert b[role]['radius']>=p['radius']
        if role.endswith('_hoof'):
            assert p['location'][:2]==b[role]['location'][:2]
            assert b[role]['location'][2]-b[role]['depth']/2==0
    assert b['-1_fore_lower']['radius']==.43


def test_fitted_rein_and_angular_pauldron_recipes():
    d=catalog()
    golden=json.loads((ROOT/'tests/fixtures/dragon-prince-fitted-reins-pauldrons-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in [flush_reins(1001),angular_pauldrons(1001)]}==golden
    assert {ref:d[ref].sha256 for ref in golden}==golden
    caps=[a for a in angular_pauldrons(1001).to_dict()['parameters']['atoms'] if a['role'].startswith('shoulder_shell_')]
    assert all(a['primitive']=='cube' and abs(a['rotation'][1])>.3 for a in caps)
    assert fitted_reins(1001).to_dict()['parameters']['landmarks']==d['aurelian.dragon-prince-reins@3'].to_dict()['parameters']['landmarks']


def test_supported_seal_stock_and_mount():
    p=supported_lance_seal(1001).to_dict()['parameters']
    atoms={a['role']:a for a in p['atoms']}
    assert not any(role.startswith('pennant_fold_') for role in atoms)
    tab=atoms['supported_seal_tab']
    assert min(tab['dimensions'][:2])-2*tab['bevel']>=.75
    assert atoms['shaft']['radius']*2==1.0
    assert p['landmarks']==catalog()['aurelian.dragon-prince-lance@2'].to_dict()['parameters']['landmarks']
    hanging=tapestry_lance(1001).to_dict()['parameters']
    folds=[a for a in hanging['atoms'] if a['role'].startswith('tapestry_fold_')]
    assert len(folds)==3
    assert all(min(a['dimensions'][:2])-2*a['bevel']>=.75 for a in folds)
    assert all(a['location'][1]-a['dimensions'][1]/2<.1 for a in folds)
    assert hanging['landmarks']==p['landmarks']


def test_shield_legs_and_scalp_revisions():
    d=catalog()
    for filename,recipe in [('heroic-steed',lambda:heroic_steed(1001)),('tapestry-lance',lambda:tapestry_lance(1001)),('bridle-fitted-reins',lambda:bridle_fitted_reins(1001)),('snug-reins',lambda:fitted_reins(1001)),('supported-seal',lambda:supported_lance_seal(1001)),('dense-scaled-shield',lambda:dense_scaled_shield(1001)),('scaled-shield',lambda:scaled_shield(1001)),('routed-reins',lambda:routed_reins(1001)),('gem-shield',lambda:gem_shield(1001)),('great-shield',lambda:great_shield(1001)),('shield',lambda:larger_shield(1001)),
                            ('flexed-horse',lambda:flexed_steed(1001)),
                            ('scalp',lambda:scalp_barding(d,1001))]:
        golden=json.loads((ROOT/f'tests/fixtures/dragon-prince-{filename}-golden.json').read_text())
        for _ in range(2):
            p=recipe();assert {p.reference:p.sha256}==golden
        assert {ref:d[ref].sha256 for ref in golden}==golden
    old={a['role']:a for a in d['aurelian.dragon-prince-horse@3'].to_dict()['parameters']['atoms']}
    new={a['role']:a for a in d['aurelian.dragon-prince-horse@4'].to_dict()['parameters']['atoms']}
    for role in old:
        if role.endswith('_hoof'):assert old[role]==new[role]
    for side in (-1,1):
        assert new[f'{side}_hind_stifle']['location'][1]<new[f'{side}_hind_hock']['location'][1]
    placements=load_assembly(ROOT/'specs/elf-dragon-prince.json',d)['placements']
    shield=next(p for p in placements if p['instance_id']=='prince-01/shield')
    assert shield['part']=='aurelian.dragon-prince-shield@6'
    assert -shield['mount'][0][1]<-.6  # Front normal points outward to rider's left.
    atoms=d['aurelian.dragon-prince-shield@4'].to_dict()['parameters']['atoms']
    assert {a['role'] for a in atoms}=={'shield','oval_gem_setting','central_oval_gem'}
    assert all(a['location'][0]==a['location'][2]==0 for a in atoms)
    rein=d['aurelian.dragon-prince-reins@3'].to_dict()['parameters']['landmarks']
    assert rein==d['aurelian.dragon-prince-reins@2'].to_dict()['parameters']['landmarks']


def test_reference_revisions_are_deterministic_and_preserve_assembly_contacts():
    d=catalog()
    golden=json.loads((ROOT/'tests/fixtures/dragon-prince-reference-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in reference_parts(d,1001)}==golden
    assert {ref:d[ref].sha256 for ref in golden}==golden
    for old,new in [('horse@1','horse@2'),('lance@1','lance@2')]:
        a,b=(d['aurelian.dragon-prince-'+r].to_dict() for r in (old,new))
        assert a['parameters']['landmarks']==b['parameters']['landmarks']
    resolved=load_assembly(ROOT/'specs/elf-dragon-prince.json',d)

    connected=json.loads((ROOT/'tests/fixtures/dragon-prince-connected-heads-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in connected_head_parts(d,1001)}==connected
    assert {ref:d[ref].sha256 for ref in connected}==connected
    scales=json.loads((ROOT/'tests/fixtures/dragon-prince-scale-helmets-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in scale_helmets(d,1001)}==scales
    assert {ref:d[ref].sha256 for ref in scales}==scales
    upright=json.loads((ROOT/'tests/fixtures/dragon-prince-upright-helmets-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in upright_helmets(d,1001)}==upright
    assert {ref:d[ref].sha256 for ref in upright}==upright
    visor=json.loads((ROOT/'tests/fixtures/dragon-prince-visor-golden.json').read_text())
    for _ in range(2):
        p=swept_visor(d,1001);assert {p.reference:p.sha256}==visor
    assert {ref:d[ref].sha256 for ref in visor}==visor
    assert set(visor).issubset({p['part'] for p in resolved['placements']})
    helmet=d['aurelian.dragon-prince-helmet@5'].to_dict()
    assert 'parent_reference' not in helmet['parameters']
    assert helmet['parameters']['operations'][-1]['operation']=='DIFFERENCE'

def test_cavalry_recipes_and_equipment_contacts():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/dragon-prince-v1-golden.json').read_text())
    assert {ref:d[ref].sha256 for ref in golden}==golden
    for _ in range(2):
        for p in cavalry_parts(d,1001):assert p.sha256==golden[p.reference]
    bard_golden=json.loads((ROOT/'tests/fixtures/dragon-prince-barding-v2-golden.json').read_text())
    for _ in range(2):
        p=open_face_barding(1001);assert p.sha256==d[p.reference].sha256==bard_golden[p.reference]
    m={p['instance_id']:p for p in load_assembly(ROOT/'specs/elf-dragon-prince.json',d)['placements']}
    def anchor(slot,name):
        p=m['prince-01/'+slot];v=d[p['part']].to_dict()['parameters']['landmarks'][name]
        return [sum(p['mount'][i][j]*v[j] for j in range(3))+p['mount'][i][3] for i in range(3)]
    assert anchor('lance','grip')==pytest.approx(anchor('right-arm','grip'))
    assert anchor('shield','grip')==pytest.approx(anchor('left-arm','grip'))
    assert m['prince-01/helmet']['mount']==m['prince-01/head']['mount']
    assert anchor('horse','ground')==[0,0,2]
    assert anchor('riding-legs','torso')==[0,0,10]

@pytest.mark.integration
def test_saved_cavalry_provenance():
    if not os.environ.get('DRAGON_PRINCE_PROOF'):pytest.skip('set DRAGON_PRINCE_PROOF for saved scene')
    path=ROOT/'out/elf-dragon-prince-heroic-steed-v1'
    p=json.loads((path/'saved-provenance.json').read_text());assert p['passes'] and all(p['checks'].values())
    review=json.loads((path/'visual-review.json').read_text());assert not review['digitally_validated']
    clearance=json.loads((path/'reins-clearance.json').read_text())
    assert clearance['passes'] and not clearance['collisions'] and clearance['revision']==6
    assert clearance['minimum_clearance_mm']['prince-01/shield']>.12
    assert 'aurelian.head@12' in review['reused_parts'] and 'aurelian.swordmaster-cuirass@1' in review['reused_parts']
    golden=json.loads((ROOT/'tests/fixtures/dragon-prince-reference-golden.json').read_text())
    connected=json.loads((ROOT/'tests/fixtures/dragon-prince-connected-heads-golden.json').read_text())
    scales=json.loads((ROOT/'tests/fixtures/dragon-prince-scale-helmets-golden.json').read_text())
    upright=json.loads((ROOT/'tests/fixtures/dragon-prince-upright-helmets-golden.json').read_text())
    visor=json.loads((ROOT/'tests/fixtures/dragon-prince-visor-golden.json').read_text())
    assert review['compiled_parts']==['aurelian.dragon-prince-horse@5']
    old=json.loads((ROOT/'out/elf-dragon-prince-plain-lance-v1/assembly-job.json').read_text())
    new=json.loads((path/'assembly-job.json').read_text())
    assert set(visor).issubset(new['assets'])
    for ref in set(new['assets']) & set(old['assets']):
        assert new['assets'][ref]['key']==old['assets'][ref]['key']
    assert {p['instance_id']:p['mount'] for p in old['assembly']['placements']}=={p['instance_id']:p['mount'] for p in new['assembly']['placements']}
