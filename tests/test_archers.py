import json
import os
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.components.parts import catalog

ROOT = Path(__file__).resolve().parent.parent


def world(placement, point):
    m = placement['mount']
    return [sum(m[i][j]*point[j] for j in range(3))+m[i][3] for i in range(3)]


def test_archer_golden_shared_recipe_and_light_equipment():
    definitions = catalog()
    for revision in (1,2,3):
        golden = json.loads((ROOT/f'tests/fixtures/archer-v{revision}-golden.json').read_text())
        assert {ref:definitions[ref].sha256 for ref in golden} == golden
    model = load_model(ROOT/'specs/models/elf-archer.json', definitions)
    solo = load_assembly(ROOT/'specs/elf-archer.json', definitions)
    unit = load_assembly(ROOT/'specs/elf-unit-archers.json', definitions)
    assert len(model['placements']) == 11
    assert len(solo['placements']) == 12 and len(unit['placements']) == 56
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
    for spec in ('elf-archer.json','elf-unit-archers.json'):
        assert {p['part'] for p in load_assembly(ROOT/'specs'/spec)['placements']} <= checked
