import json
import os
from pathlib import Path
import pytest

from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.garment_trims import garment_trim, cape_fitted_mail_trim
from fdm_sculpt.components.parts import catalog

ROOT=Path(__file__).resolve().parent.parent
NAMES=['elf-modular-visual','elf-standard-bearer','elf-unit-center-standard','elf-archer','elf-unit-archers','elf-archer-variants','elf-archer-sergeant','elf-spearman-variants','elf-spearman-hawk-sergeant']


def test_trim_recipes_and_army_mounts():
    definitions=catalog()
    for revision in (1,2):
        golden=json.loads((ROOT/f'tests/fixtures/garment-trims-v{revision}-golden.json').read_text())
        for kind in ('tunic','mail-skirt'):
            for _ in range(2):
                d=garment_trim(kind,seed=1001,revision=revision)
                assert d.sha256==definitions[d.reference].sha256==golden[d.reference]
            p=d.to_dict()['parameters']
            assert [o['operation'] for o in p['operations']]==['DIFFERENCE','UNION','DIFFERENCE','DIFFERENCE','DIFFERENCE']
    count=0
    for name in NAMES:
        assembly=load_assembly(ROOT/f'specs/{name}.json',definitions)
        slots={p['instance_id']:p for p in assembly['placements']}
        for p in assembly['placements']:
            if not p['part'].startswith(('aurelian.archer-tunic@','aurelian.skirt@')):continue
            if p['part'].startswith('aurelian.archer-tunic@'):
                assert p['instance_id']+'-trim' not in slots
                continue
            trim=slots[p['instance_id']+'-trim']
            assert trim['mount']==p['mount']
            cape=slots[p['instance_id'].replace('/skirt','/cape')]
            cape_source=definitions[cape['part']].to_dict()['parameters'].get('robe_source',cape['part'])
            assert definitions[trim['part']].to_dict()['parameters']['cape_reference']==cape_source
            count+=1
        if 'archer' in name:
            assert not any('skirt-trim' in p['instance_id'] for p in assembly['placements'])
    assert count==22


@pytest.mark.parametrize('revision',[5,6])
def test_cape_contact_goldens(revision):
    definitions=catalog()
    golden=json.loads((ROOT/f'tests/fixtures/mail-trim-v{revision}-golden.json').read_text())
    for suffix in ('','-b','-c','-d','-e'):
        cape=definitions['aurelian.cape'+suffix+'@2']
        for _ in range(2):
            trim=cape_fitted_mail_trim(cape,seed=1001,revision=revision)
            assert trim.sha256==definitions[trim.reference].sha256==golden[trim.reference]


def test_mail_trim_wrap_and_cape_revisions():
    definitions=catalog()
    for revision in (3,4):
        golden=json.loads((ROOT/f'tests/fixtures/mail-trim-v{revision}-golden.json').read_text())
        for _ in range(2):
            d=garment_trim('mail-skirt',seed=1001,revision=revision)
            assert d.sha256==definitions[d.reference].sha256==golden[d.reference]
        atoms={a['role']:a for a in d.to_dict()['parameters']['atoms']}
        stop=atoms['waist_wrap_limit']
        assert stop['location'][2]+stop['dimensions'][2]/2==-1.25
        if revision==4:
            stop=atoms['cape_clearance_limit']
            assert stop['location'][1]+stop['dimensions'][1]/2==-.5


@pytest.mark.integration
def test_saved_trim_scenes():
    if not os.environ.get('GARMENT_TRIM_PROOFS'):
        pytest.skip('set GARMENT_TRIM_PROOFS for saved army reviews')
    checked=set()
    for name in NAMES:
        suffix='trim-contact-v6'
        output=ROOT/f'out/{name}-{suffix}'
        proof=json.loads((output/'saved-provenance.json').read_text())
        review=json.loads((output/'visual-review.json').read_text())
        job=json.loads((output/'assembly-job.json').read_text())
        assert proof['passes'] and all(proof['checks'].values())
        assert not review['digitally_validated'] and not review['compiled_parts']
        previous='garment-trims-v2' if 'archer' in name else 'trim-clearance-v4'
        old=json.loads((ROOT/f'out/{name}-{previous}/assembly-job.json').read_text())
        def figure_parts(record):
            return [p for p in record['assembly']['placements'] if '-trim@' not in p['part'] and 'mail-skirt-trim' not in p['part']]
        assert figure_parts(job)==figure_parts(old)
        for ref,asset in old['assets'].items():
            if ref in job['assets']:assert job['assets'][ref]['key']==asset['key']
        checked.update(job['assets'])
    assert {'aurelian.mail-skirt-trim'+s+'@6' for s in ('','-b','-c','-d','-e')}<=checked
    assert not any('tunic-trim' in ref for ref in checked)
