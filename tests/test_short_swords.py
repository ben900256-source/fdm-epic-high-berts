import json
import math
from pathlib import Path

from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.swords import short_sword

ROOT = Path(__file__).resolve().parent.parent


def test_longer_sword_golden_and_forward_spearman_poses():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/short-sword-v2-golden.json').read_text())
    for _ in range(2):
        sword = short_sword(seed=1001)
        assert sword.sha256 == definitions[sword.reference].sha256 == golden[sword.reference]
    p = sword.to_dict()['parameters']
    assert p['landmarks']['grip'] == definitions['aurelian.shortblade@1'].to_dict()['parameters']['landmarks']['grip']
    assert p['design']['grip_length_mm'] == 1.9
    assert p['design']['blade_length_mm'] > 3.5
    assert p['landmarks']['tip'][2] > 4.5
    assert all(o['solver']=='EXACT' for o in p['operations'])
    swords = 0
    for path in (ROOT/'specs/models/spearmen').glob('*.json'):
        recipe = json.loads(path.read_text())
        assert abs(math.degrees(math.atan2(recipe['transform'][1][0], recipe['transform'][0][0]))) <= 5.001
        for slot in load_model(path, definitions)['placements']:
            if slot['instance_id']=='head':
                # Includes both the inherited stance and the added pose turns.
                m = slot['mount']
                assert abs(math.degrees(math.atan2(-m[0][1], m[1][1]))) <= 10.001
            if slot['instance_id']=='shortblade':
                assert slot['part']==sword.reference
                swords += 1
    assert swords == 4
