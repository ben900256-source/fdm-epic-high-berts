import json
import math
from pathlib import Path
import pytest
from fdm_sculpt.army import load_model
from fdm_sculpt.components.archer_elevation import elevated_arm
from fdm_sculpt.components.parts import catalog

ROOT=Path(__file__).resolve().parent.parent

def world(p,v):return [sum(p['mount'][i][j]*v[j] for j in range(3))+p['mount'][i][3] for i in range(3)]

def test_elevated_archers_keep_shoulders_and_grips_aligned():
    d=catalog();golden=json.loads((ROOT/'tests/fixtures/archer-elevation-v1-golden.json').read_text())
    base={p['instance_id']:p for p in load_model(ROOT/'specs/models/archers/01-aiming-forward.json',d)['placements']}
    for number,degrees in enumerate((20,30,40),11):
        m={p['instance_id']:p for p in load_model(ROOT/f'specs/models/archers/{number}-aiming-up-{degrees}.json',d)['placements']}
        def anchor(slot,name):return world(m[slot],d[m[slot]['part']].to_dict()['parameters']['landmarks'][name])
        for slot,name in [('bow-arm','grip'),('draw-arm','nock')]:
            historical=d[f'aurelian.archer-{slot}-elevated-{degrees}@1']
            parent=d[historical.to_dict()['parameters']['parent_reference']]
            for _ in range(2):
                arm=elevated_arm(parent,degrees=degrees,seed=1001)
                assert arm.sha256==d[arm.reference].sha256==golden[arm.reference]
            shoulder=d[base[slot]['part']].to_dict()['parameters']['landmarks']['shoulder']
            assert anchor(slot,'shoulder')==pytest.approx(world(base[slot],shoulder))
            assert anchor(slot,'grip')==pytest.approx(anchor('bow',name))
        assert anchor('arrow','nock')==pytest.approx(anchor('bow','nock'))
        assert anchor('bow-ferrule','grip')==pytest.approx(anchor('bow','grip'))
        tip,nock=anchor('arrow','tip'),anchor('arrow','nock')
        assert math.degrees(math.atan2(tip[2]-nock[2],nock[1]-tip[1]))==pytest.approx(degrees+math.degrees(math.atan2(.05,2.22)))
        for slot in ('left-leg','right-leg','tunic','quiver'):assert m[slot]==base[slot]
        for slot in m:
            if slot not in ('bow-arm','draw-arm'):assert m[slot]['part']==base[slot]['part']
