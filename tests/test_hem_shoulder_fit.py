import json
import math
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.components.hem_shoulder_fit import revised_parts
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.workshop import models

ROOT = Path(__file__).resolve().parents[1]


def test_fit_goldens_and_preserved_upper_skirt():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/hem-shoulder-fit-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in revised_parts(definitions, 1001)} == golden
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    current = definitions['aurelian.skirt@8'].to_dict()['parameters']
    previous = definitions['aurelian.skirt@7'].to_dict()['parameters']
    assert current['operations'] == previous['operations']
    for before, after in zip(previous['atoms'], current['atoms']):
        if before['role'] != 'hem_ground_transition':
            assert before == after
        else:
            assert after['location'][2]+after['depth']/2 == pytest.approx(before['location'][2]+before['depth']/2)
            assert after['radius2'] == before['radius2']
            assert (after['radius2']-after['radius1'])/after['depth'] == pytest.approx((before['radius2']-before['radius1'])/before['depth'])


def test_historical_inherited_shoulders_are_centered_in_plate_holes():
    definitions = catalog()
    count = 0
    sources=json.loads((ROOT/'specs/accepted-army-sources.json').read_text())['sources']
    for model in models():
        key=Path(model['path']).relative_to(ROOT).as_posix()
        slots = {p['instance_id'].split('/')[-1]:p for p in sources[key]['placements']}
        for side in ('left', 'right'):
            if side+'-tunic' not in slots or 'mail' not in slots:
                continue
            pad, plate = slots[side+'-tunic'], slots['mail']
            # The left cloth sleeve now follows the posed arm below the hole;
            # its placement is checked against that axis separately below.
            if side=='left' and pad['part']=='aurelian.left-tunic@6':
                continue
            anchors = definitions[plate['part']].to_dict()['parameters']['landmarks']
            if side+'_armhole' not in anchors:
                continue
            target = point(plate['mount'], anchors[side+'_armhole'])
            landmarks = definitions[pad['part']].to_dict()['parameters']['landmarks']
            center = point(pad['mount'], landmarks.get(side+'_shoulder', landmarks.get(side+'_pauldron')))
            assert math.dist(target, center) < 1e-6, (model['id'], side)
            count += 1
    assert count >= 10


def test_historical_left_sleeves_are_integrated_with_the_posed_arm():
    from fdm_sculpt.components.robe_arms import pose
    definitions=catalog()
    assembly=json.loads((ROOT/'specs/accepted-army-sources.json').read_text())['sources']['specs/elf-modular-visual.json']
    slots={p['instance_id']:p for p in assembly['placements']}
    for i in range(1,6):
        arm=slots[f'elf-{i:02}/left-arm']
        assert f'elf-{i:02}/left-tunic' not in slots
        params=definitions[arm['part']].to_dict()['parameters']
        source=definitions[params['robe_source']]
        shoulder,elbow,wrist=pose(source)
        assert params['cloth_pose']==dict(shoulder=shoulder,elbow=elbow,wrist=wrist)
        assert 'robe_sleeve' in definitions[arm['part']].output_roles
