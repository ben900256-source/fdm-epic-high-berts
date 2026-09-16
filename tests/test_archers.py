import json
import os
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.atelier import prepare
from fdm_sculpt.components.elves_v2 import multiply
from fdm_sculpt.components.parts import catalog

ROOT = Path(__file__).resolve().parent.parent


def world(placement, point):
    m = placement['mount']
    return [sum(m[i][j]*point[j] for j in range(3))+m[i][3] for i in range(3)]


def test_archer_golden_shared_recipe_and_light_equipment():
    definitions = catalog()
    for revision in (1,2,3,4):
        golden = json.loads((ROOT/f'tests/fixtures/archer-v{revision}-golden.json').read_text())
        assert {ref:definitions[ref].sha256 for ref in golden} == golden
    model = load_model(ROOT/'specs/models/elf-archer.json', definitions)
    solo = load_assembly(ROOT/'specs/elf-archer.json', definitions)
    unit = load_assembly(ROOT/'specs/elf-unit-archers.json', definitions)
    assert len(model['placements']) == 12
    assert len(solo['placements']) == 14 and len(unit['placements']) == 62
    assert not any(p['part'].split('@')[0] in {
        'aurelian.skirt','aurelian.chest-plate','aurelian.shield','aurelian.spear'
    } for p in model['placements'])
    for index in range(5):
        placements = [p for p in unit['placements'] if p['instance_id'].startswith(f'archer-{index+1:02d}/')]
        assert {p['part'] for p in placements} == {p['part'] for p in model['placements']}


def test_side_on_stance_and_bow_hand_alignment():
    definitions = catalog()
    model = {p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-archer.json', definitions)['placements']}
    # Local garment front (-Y) points sideways (+X); head still faces forward (-Y).
    assert model['tunic']['mount'][0][1] < -.99
    assert model['head']['mount'][1][1] > .99
    bow = definitions[model['bow']['part']].to_dict()['parameters']['landmarks']
    for name,anchor in [('bow-arm','grip'),('draw-arm','nock')]:
        arm = definitions[model[name]['part']].to_dict()['parameters']['landmarks']
        assert world(model[name],arm['grip']) == pytest.approx(world(model['bow'],bow[anchor]))
    assert world(model['arrow'],[0,0,0]) == pytest.approx(world(model['bow'],bow['nock']))


def test_thirteen_variants_share_parts_and_have_the_requested_equipment():
    definitions = catalog()
    for revision in (1,2,3):
        golden = json.loads((ROOT/f'tests/fixtures/archer-variants-v{revision}-golden.json').read_text())
        assert {ref:definitions[ref].sha256 for ref in golden} == golden
    index = json.loads((ROOT/'specs/archer-variants-index.json').read_text())['variants']
    assert len(index) == 13
    assert len({v['model'] for v in index}) == 13
    counts = {'arrow':0,'held-arrow':0,'shortblade':0}
    for variant in index:
        model = {p['instance_id']:p for p in load_model(ROOT/'specs'/variant['model'],definitions)['placements']}
        assert model['bow-ferrule']['part'] == 'aurelian.archer-bow-ferrule@3'
        assert model['tunic']['part'] == 'aurelian.archer-tunic@5'
        for slot in counts:
            counts[slot] += slot in model
        if variant['state'] == 'nocked':
            bow = definitions[model['bow']['part']].to_dict()['parameters']['landmarks']
            arm = definitions[model['draw-arm']['part']].to_dict()['parameters']['landmarks']
            assert world(model['arrow'],[0,0,0]) == pytest.approx(world(model['bow'],bow['nock']))
            assert world(model['draw-arm'],arm['grip']) == pytest.approx(world(model['bow'],bow['nock']))
        else:
            assert model['bow']['part'] == 'aurelian.archer-bow@5'
    assert counts == {'arrow':6,'held-arrow':1,'shortblade':2}
    gallery = load_assembly(ROOT/'specs/elf-archer-variants.json',definitions)
    assert len(gallery['placements']) == 178


def test_preserved_supports_removed_and_new_ferrule_golden():
    definitions = catalog()
    fixtures = [f'archer-arrow-support-v{i}-golden.json' for i in (1,2,3)]
    fixtures.append('archer-bow-ferrule-v2-golden.json')
    fixtures.append('war-horn-v7-golden.json')
    fixtures.append('archer-sergeant-v2-golden.json')
    fixtures.append('archer-sergeant-v3-golden.json')
    fixtures.extend(['archer-sergeant-v1-golden.json','archer-lowered-bows-v1-golden.json','boots-v4-golden.json'])
    for name in fixtures:
        golden = json.loads((ROOT/'tests/fixtures'/name).read_text())
        assert {ref:definitions[ref].sha256 for ref in golden} == golden
    for path in (ROOT/'specs/models/archers').glob('*.json'):
        assert all(p['instance_id'] != 'arrow-support' for p in load_model(path,definitions)['placements'])


def test_sergeant_horn_mouth_and_lowered_bow_grips():
    definitions = catalog()
    model = {p['instance_id']:p for p in load_model(ROOT/'specs/models/elf-archer-sergeant.json',definitions)['placements']}
    def anchor(slot,name):
        return world(model[slot],definitions[model[slot]['part']].to_dict()['parameters']['landmarks'][name])
    assert anchor('horn','mouthpiece') == pytest.approx(anchor('head','mouth_line'))
    assert anchor('horn','grip') == pytest.approx(anchor('horn-arm','grip'))
    assert anchor('bow','grip') == pytest.approx(anchor('bow-arm','grip'))
    assert anchor('bow','grip')[0] < -2
    for filename,height in [('05-ready-turned.json',6.9),('07-drawing-arrow.json',6.25)]:
        model = {p['instance_id']:p for p in load_model(ROOT/'specs/models/archers'/filename,definitions)['placements']}
        assert anchor('bow','grip') == pytest.approx(anchor('bow-arm','grip'))
        assert anchor('bow','grip')[2] == pytest.approx(height)


def test_pose_transforms_preserve_shared_geometry_cache_keys(tmp_path):
    first = load_model(ROOT/'specs/models/archers/01-aiming-forward.json')
    second = load_model(ROOT/'specs/models/archers/02-aiming-left.json')
    base = {p['instance_id']:p for p in first['placements']}
    turned = {p['instance_id']:p for p in second['placements']}
    recipe = json.loads((ROOT/'specs/models/archers/02-aiming-left.json').read_text())
    assert turned['head']['mount'] == multiply(recipe['transform'],base['head']['mount'])
    assert turned['bow']['mount'] == multiply(recipe['transform'],multiply(recipe['transforms']['bow'],base['bow']['mount']))
    jobs = [prepare(model,seed=1001,cache=tmp_path) for model in (first,second)]
    # The turned bow needs a hand-only grip revision; every other part is reused.
    for slot in base:
        if slot=='bow-arm':
            assert base[slot]['part'] != turned[slot]['part']
        else:
            ref=base[slot]['part']
            assert ref==turned[slot]['part']
            assert jobs[0]['assets'][ref]['key']==jobs[1]['assets'][ref]['key']


def test_model_transforms_reject_unknown_slots_and_nonrigid_matrices(tmp_path):
    spec = json.loads((ROOT/'specs/models/archers/02-aiming-left.json').read_text())
    spec['source']['assembly'] = str(ROOT/'specs/elf-archer.json')
    path = tmp_path/'variant.json'
    spec['transforms']['missing-slot'] = spec['transform']
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='unknown model slot'):
        load_model(path)
    del spec['transforms']['missing-slot']
    spec['transform'][0][0] = 2
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        load_model(path)


@pytest.mark.integration
def test_saved_archer_provenance():
    outputs = os.environ.get('ARCHER_PROOF_BUILDS')
    if not outputs:
        pytest.skip('set ARCHER_PROOF_BUILDS to standalone and unit directories separated by semicolons')
    checked = set()
    for name in outputs.split(';'):
        output = Path(name)
        provenance = json.loads((output/'saved-provenance.json').read_text())
        job = json.loads((output/'assembly-job.json').read_text())
        review = json.loads((output/'visual-review.json').read_text())
        assert provenance['passes'] and all(provenance['checks'].values())
        assert not review['digitally_validated']
        assert review['placements'] == len(job['assembly']['placements'])
        checked.update(job['assets'])
    for spec in ('elf-archer.json','elf-unit-archers.json','elf-archer-variants.json'):
        assert {p['part'] for p in load_assembly(ROOT/'specs'/spec)['placements']} <= checked
