import json
from copy import deepcopy
from pathlib import Path

import pytest

from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.components.leaning_spears import apply, lean_degrees
from test_accepted_army import Definitions

ROOT = Path(__file__).resolve().parents[1]


def test_locked_five_change_only_upright_spear_mounts_and_keep_grip_pivots():
    old = json.loads((ROOT/'specs/baselines/spearmen-printed-20260923.json').read_text(encoding='utf-8'))
    updated = deepcopy(old)
    changes = apply(updated, Definitions())
    assert len(changes) == 3
    originals = {p['instance_id']: p for p in old['placements']}
    current = json.loads((ROOT/'specs/elf-modular-visual.json').read_text(encoding='utf-8'))
    assert current['placements'] == updated['placements']
    for p in updated['placements']:
        previous = originals[p['instance_id']]
        if not p['instance_id'].endswith('/spear') or lean_degrees(previous['mount']) >= 6:
            assert p == previous
        else:
            assert p['part'] == previous['part']
            assert p['definition_sha256'] == previous['definition_sha256']
            assert lean_degrees(p['mount']) == pytest.approx(6, abs=1e-6)
    for change in changes:
        spear = next(p for p in updated['placements'] if p['instance_id'] == change['figure']+'/spear')
        assert point(spear['mount'], change['local_pivot_mm']) == pytest.approx(change['grip_axis_pivot_mm'], abs=1e-7)
    repeated = deepcopy(updated)
    assert apply(repeated, Definitions()) == []
    assert repeated == updated


def test_every_current_spear_has_a_visible_lean():
    index = json.loads((ROOT/'specs/accepted-army-index.json').read_text(encoding='utf-8'))
    paths = [ROOT/name for name in index['assemblies']]
    paths += list((ROOT/'specs/accepted-army-models').glob('*.json'))
    count = 0
    for path in paths:
        spec = json.loads(path.read_text(encoding='utf-8'))
        for p in spec['placements']:
            if p['instance_id'].endswith('/spear'):
                assert lean_degrees(p['mount']) >= 6 - 1e-6, (path, p['instance_id'])
                count += 1
    assert count == 41
