import json
from copy import deepcopy
from pathlib import Path
import pytest
from fdm_sculpt.components.grip_spears import (assemblies, BOTTOM_Z, BED_AXIS_Z, clearance_profile, point, CHANNEL_BACK, CHANNEL_LIP, RECESS_DEPTH, BACKING_STOCK)
from fdm_sculpt.components.parts import catalog, inverse_rigid, resolve_assembly
ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def trial():
    saved = catalog()
    source = json.loads((ROOT/'specs/experiments/full-spear-source-row.json').read_text())
    targets = json.loads((ROOT/'specs/experiments/open-grip-clearance-targets.json').read_text())
    parts, specs = assemblies(source, saved, targets)
    return saved, source, targets, parts, specs

def test_parts_assemblies_and_golden_hashes_are_pinned(trial):
    saved, _, _, parts, specs = trial
    golden = json.loads((ROOT/'tests/fixtures/open-grip-spears-tapered-v11-golden.json').read_text())
    assert {p.reference: p.sha256 for p in parts} == golden
    for part in parts:
        assert saved[part.reference].to_dict() == part.to_dict()
    for spec in specs:
        assert resolve_assembly(spec, saved)['placements'] == spec['placements']
        assert json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text()) == spec
    empty, kit, assembled = specs
    assert len(empty['placements']) == 90
    assert assembled['placements'][:90] == empty['placements']
    assert len(assembled['placements']) == 95
    assert len(kit['placements']) == 6
    assert all('socket' not in p['part'] and 'insert-trial' not in p['part'] for p in assembled['placements'])

def test_axes_cross_original_finger_centers_without_changing_poses(trial):
    saved, _, _, parts, (_, _, assembled) = trial
    baseline = json.loads((ROOT/'tests/fixtures/open-grip-pose-baseline.json').read_text())
    by_id = {p['instance_id']: p for p in assembled['placements']}
    for i, hand in enumerate(parts[2:7], 1):
        arm = by_id[f'row-{i:02}/right-arm']
        spear = by_id[f'row-{i:02}/separate-spear']
        assert arm['mount'] == baseline[arm['instance_id']]
        # Print-space Y is the length axis. Only the flat-back roll changes.
        assert [r[1] for r in spear['mount'][:3]] == pytest.approx([r[1] for r in baseline[spear['instance_id']][:3]], abs=1e-8)
        params = hand.to_dict()['parameters']
        original = saved[params['open_grip_trial']['source']].to_dict()['parameters']
        center = point(arm['mount'], original['landmarks']['right_grouped_fingers'])
        printed = point(inverse_rigid(spear['mount']), center)
        assert printed[0] == pytest.approx(0, abs=.00001)
        assert printed[2] == pytest.approx(BED_AXIS_Z, abs=.00001)
        assert 0 < printed[1] < 13.6
        old = baseline[spear['instance_id']]
        translation = [spear['mount'][j][3]-old[j][3] for j in range(3)]
        assert sum(translation[j]*old[j][1] for j in range(3)) == pytest.approx(0, abs=1e-7)

def test_sleeve_and_attachment_landmarks_preserved_with_deeper_hand(trial):
    saved, _, _, parts, _ = trial
    for hand in parts[2:7]:
        params = hand.to_dict()['parameters']
        original = saved[params['open_grip_trial']['source']].to_dict()['parameters']
        old_ops = [o for o in original['operations'] if o['target'] == 'robe_sleeve']
        old_roles = {'robe_sleeve'} | {o['operand'] for o in old_ops}
        assert [a for a in params['atoms'] if a['role'] in old_roles] == [a for a in original['atoms'] if a['role'] in old_roles]
        assert params['operations'][:len(old_ops)] == old_ops
        assert params['landmarks']['right_cuff'] == original['landmarks']['right_cuff']
        heel = next(a for a in params['atoms'] if a['role'] == 'palm_heel')
        assert point(heel['frame_mm'], heel['start']) == pytest.approx(original['landmarks']['right_cuff'], abs=1e-7)
        assert RECESS_DEPTH == pytest.approx(CHANNEL_LIP-CHANNEL_BACK)
        palm = next(a for a in params['atoms'] if a['role'] == 'right_palm')
        assert palm['location'][0]-palm['dimensions'][0]/2 == pytest.approx(CHANNEL_BACK-BACKING_STOCK)
        assert palm['location'][0]+palm['dimensions'][0]/2 > CHANNEL_BACK+.05
        assert BACKING_STOCK == .75
        assert len([a for a in params['atoms'] if a['role'].startswith('curled_finger_')]) == 4
        assert any(a['role']=='finger_stock' for a in params['atoms'])
        assert params['open_grip_trial']['finger_root_mm'] == .5

def test_full_spear_and_clearance_envelope(trial):
    _, _, _, parts, _ = trial
    trial_data = parts[0].to_dict()['parameters']['trial']
    assert BOTTOM_Z+trial_data['length_mm'] == pytest.approx(8.75)
    assert parts[0].reference == 'aurelian.full-rounded-grip-spear-trial@2'
    assert parts[1].reference == 'aurelian.full-rounded-grip-spear-frame-trial@2'
    shaft, head = clearance_profile()
    assert shaft[2]*2-trial_data['shaft_diameter_mm'] == pytest.approx(.2)
    assert -.3-shaft[0] == pytest.approx(.1)
    assert shaft[3] < BOTTOM_Z and head[4] > 8.75
    assert head[2] >= .92+.1

def test_only_intersected_neighbors_receive_local_clearance(trial):
    saved, source, targets, parts, (_, _, assembled) = trial
    source_by_id = {p['instance_id']: p for p in source['placements']}
    for p in assembled['placements']:
        key = p['instance_id']
        if not key.endswith(('/right-arm', '/separate-spear')):
            expected = deepcopy(source_by_id[key]['mount'])
            expected[1][3] += {'row-01': .25, 'row-02': -.4, 'row-05': -.45}.get(key.split('/')[0], 0)
            assert p['mount'] == expected
        if key in targets or key.endswith(('/right-arm', '/separate-spear')):
            continue
        assert p['part'] == source_by_id[key]['part']
    for part in parts[7:]:
        params = part.to_dict()['parameters']
        info = params['centered_grip_clearance']
        original = saved[info['source']].to_dict()['parameters']
        assert params['atoms'][:len(original['atoms'])] == original['atoms']
        for cut in info['cuts']:
            assert set(cut['roles']) <= set(saved[info['source']].output_roles)
        assert all(o['operation'] == 'DIFFERENCE' for o in params['operations'][len(original['operations']):])


def test_stale_neighbor_hash_is_rejected(trial):
    saved, source, targets, _, _ = trial
    stale = deepcopy(targets)
    next(iter(stale.values()))[0]['source_sha256'] = '0'*64
    with pytest.raises(ValueError, match='stale clearance target'):
        assemblies(source, saved, stale)
