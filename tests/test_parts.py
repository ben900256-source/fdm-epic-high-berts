from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

import pytest

from fdm_sculpt import atelier
from fdm_sculpt.components.core import ComponentDefinition
from fdm_sculpt.components.elves import ELF_V11_DEFINITIONS
from fdm_sculpt.components.elves_v2 import identity, multiply, translation
from fdm_sculpt.components.parts import catalog, cache_key, isolated_part, resolve_assembly, rigid_matrix

ROOT = Path(__file__).resolve().parent.parent


def test_standalone_parts_match_golden_and_original_assembly():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/parts-v1-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    raw = json.loads((ROOT/'specs/elf-modular-v1.json').read_text())
    resolved = resolve_assembly(raw, definitions)
    assert len(resolved['placements']) == 86
    for index, original in enumerate(ELF_V11_DEFINITIONS):
        reconstructed, operations = {}, []
        for placement in resolved['placements']:
            if not placement['instance_id'].startswith(f'elf-{index+1:02d}/'):
                continue
            p = definitions[placement['part']].to_dict()['parameters']
            operations.extend(p['operations'])
            for atom in p['atoms']:
                atom = deepcopy(atom)
                atom['frame_mm'] = multiply(placement['mount'], atom.get('frame_mm', identity()))
                assert atom['role'] not in reconstructed
                reconstructed[atom['role']] = atom
        source = original.to_dict()['parameters']
        assert len(reconstructed) == len(source['atoms'])
        for atom in source['atoms']:
            actual = reconstructed[atom['role']]
            assert {k:v for k,v in actual.items() if k != 'frame_mm'} == {k:v for k,v in atom.items() if k != 'frame_mm'}
            expected = multiply(translation([-8+4*index,0,1]), atom.get('frame_mm', identity()))
            for a,b in zip(actual['frame_mm'], expected):
                assert a == pytest.approx(b, abs=1e-8)
        # Independent targets may move between parts; each target's Exact
        # sequence must retain its original order and operands.
        for role in reconstructed:
            assert [o for o in operations if o['target'] == role] == [o for o in source['operations'] if o['target'] == role]


def test_taller_spear_preserves_foot_width_and_tip_shape():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/spear-v2-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    old = definitions['aurelian.spear@1'].to_dict()['parameters']
    new = definitions['aurelian.spear@2'].to_dict()['parameters']
    first,second = old['atoms'][0],new['atoms'][0]
    assert second['start'] == first['start']
    assert second['radius'] == first['radius']
    assert second['frame_mm'] == first['frame_mm']
    assert second['end'][2]-second['start'][2] == pytest.approx(1.25*(first['end'][2]-first['start'][2]))
    extension = second['end'][2]-first['end'][2]
    for before,after in zip(old['atoms'][1:],new['atoms'][1:]):
        assert {k:v for k,v in before.items() if k != 'location'} == {k:v for k,v in after.items() if k != 'location'}
        assert after['location'] == pytest.approx([*before['location'][:2],before['location'][2]+extension])
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()),definitions)
    assert sum(p['part']=='aurelian.spear@3' for p in assembly['placements']) == 5


def test_collared_spear_and_buried_helmet_join():
    definitions = catalog()
    for name in ('spear-v3-golden.json', 'helmet-v3-golden.json', 'helmet-v4-golden.json', 'helmet-v5-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/name).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    spear = definitions['aurelian.spear@3'].to_dict()['parameters']
    assert spear['atoms'][:3] == definitions['aurelian.spear@2'].to_dict()['parameters']['atoms']
    old = definitions['aurelian.helmet@2'].to_dict()['parameters']['atoms']
    new = definitions['aurelian.helmet@3'].to_dict()['parameters']['atoms']
    assert new[:3] == old[:3]
    before, after = old[-1], new[-1]
    assert after['location'][2]+after['depth']/2 == pytest.approx(before['location'][2]+before['depth']/2)
    assert (after['radius1']-after['radius2'])/after['depth'] == pytest.approx((before['radius1']-before['radius2'])/before['depth'])


def cache_records(job):
    for asset in job['assets'].values():
        directory = Path(asset['directory'])
        directory.mkdir(parents=True)
        (directory/'part.blend').write_bytes(b'test cache integrity payload')
        (directory/'asset.json').write_text(json.dumps(dict(
            key=asset['key'], definition_sha256=ComponentDefinition.from_dict(asset['definition']).sha256,
            blend_sha256=hashlib.sha256((directory/'part.blend').read_bytes()).hexdigest())))


def test_single_changed_part_only_invalidates_that_part(tmp_path):
    definitions = catalog()
    data = json.loads((ROOT/'specs/elf-modular-v1.json').read_text())
    cold = atelier.prepare(data, seed=1001, cache=tmp_path, definitions=definitions)
    cache_records(cold)
    moved = deepcopy(data)
    moved['placements'][1]['mount'][0][3] += 2
    warm = atelier.prepare(moved, seed=2002, cache=tmp_path, definitions=definitions)
    assert all(a['cached'] for a in warm['assets'].values())
    revised = definitions['aurelian.crest@1'].to_dict()
    revised['version'] = 2
    revised['parameters']['atoms'][0]['dimensions'][0] += 0.1
    replacement = ComponentDefinition.from_dict(revised)
    definitions[replacement.reference] = replacement
    for placement in moved['placements']:
        if placement['part'] == 'aurelian.crest@1':
            placement.update(part=replacement.reference, definition_sha256=replacement.sha256)
    changed = atelier.prepare(moved, seed=1001, cache=tmp_path, definitions=definitions)
    assert [ref for ref,a in changed['assets'].items() if not a['cached']] == ['aurelian.crest@2']
    assert sum(a['cached'] for a in changed['assets'].values()) == 41
    assert cache_key(replacement, 'engine-a') != cache_key(replacement, 'engine-b')


def test_reject_changed_pin_and_corrupt_cache(tmp_path):
    part = isolated_part('aurelian.crest@1')
    corrupted = deepcopy(part)
    corrupted['placements'][0]['definition_sha256'] = 'bad'
    with pytest.raises(ValueError, match='pinned definition changed'):
        resolve_assembly(corrupted)
    job = atelier.prepare(part, seed=1001, cache=tmp_path)
    cache_records(job)
    asset = next(iter(job['assets'].values()))
    (Path(asset['directory'])/'part.blend').write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='integrity'):
        atelier.prepare(part, seed=1001, cache=tmp_path)
    with pytest.raises(ValueError, match='explicit integer'):
        atelier.prepare(part, seed=True, cache=tmp_path)


def test_mounts_reject_scale_and_reflection():
    for value in (2, -1):
        matrix = identity()
        matrix[0][0] = value
        with pytest.raises(ValueError):
            rigid_matrix(matrix)


def test_contoured_crest_revision_and_centered_masks():
    definitions = catalog()
    crest = definitions['aurelian.crest@2']
    golden = json.loads((ROOT/'tests/fixtures/crest-v2-golden.json').read_text())
    assert golden == {crest.reference: crest.sha256}
    p = crest.to_dict()['parameters']
    atoms = {a['role']: a for a in p['atoms']}
    leaf = atoms['helmet_leaf_crest_outline']
    stripe = atoms['helmet_crest_spine_outline']
    assert leaf['location'] == stripe['location']
    assert leaf['location'][0] == 0
    assert stripe['dimensions'][0] < leaf['dimensions'][0]
    for role in crest.output_roles:
        assert [o['operation'] for o in p['operations'] if o['target'] == role] == ['DIFFERENCE','INTERSECT','INTERSECT']
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    assert sum(p['part'] == 'aurelian.crest@4' for p in assembly['placements']) == 5


def test_smooth_plate_and_chainmail_skirt_revisions():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/plate-mail-skirt-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    plate = definitions['aurelian.chest-plate@1'].to_dict()['parameters']
    assert len(plate['atoms']) == 1 and not plate['operations']
    skirt = definitions['aurelian.skirt@2'].to_dict()['parameters']
    assert len(skirt['operations']) == 6*26
    assert all(o['operation'] == 'DIFFERENCE' and o['solver'] == 'EXACT' for o in skirt['operations'])
    assert not any('lame' in a['role'] for a in skirt['atoms'])
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for ref in ('aurelian.chest-plate@4', 'aurelian.skirt@3'):
        assert sum(p['part'] == ref for p in assembly['placements']) == 5
    assert not any(p['part'] == 'aurelian.mail@1' for p in assembly['placements'])


def test_broader_shields_curved_armor_and_bold_face_revisions():
    definitions = catalog()
    for filename in ('shield-v2-golden.json','curved-armor-v2-golden.json','head-v2-golden.json','head-v3-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/filename).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    shield = definitions['aurelian.shield@2'].to_dict()['parameters']
    assert shield['atoms'][0]['dimensions'][0] == pytest.approx(2.48*1.08)
    assert shield['atoms'][0]['dimensions'][2] == pytest.approx(4.55*1.06)
    assert shield['landmarks']['point'][2] == -2.275
    plate = definitions['aurelian.chest-plate@2'].to_dict()['parameters']
    assert plate['atoms'][0]['primitive'] == 'sphere'
    assert {o['operand'] for o in plate['operations']} >= {'left_armhole','right_armhole','neckline'}
    head = definitions['aurelian.head@3'].to_dict()['parameters']
    atoms = {a['role']:a for a in head['atoms']}
    assert 'mouth_line' not in atoms and 'brow_ridge' in atoms
    assert atoms['nose_plane']['vertices'] == 4 and atoms['nose_plane']['radius1'] > .24
    assert atoms['chin']['dimensions'][0] > .94
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for ref in ('aurelian.shield@2','aurelian.shield-insignia@2','aurelian.chest-plate@4',
                'aurelian.torso@2','aurelian.left-tunic@2','aurelian.right-tunic@2','aurelian.head@12'):
        assert sum(p['part'] == ref for p in assembly['placements']) == 5


def test_organic_face_revisions_preserve_nose_and_remove_box_shapes():
    definitions = catalog()
    for filename in ('head-v4-golden.json','head-v5-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/filename).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    head = definitions['aurelian.head@5'].to_dict()['parameters']
    atoms = {a['role']:a for a in head['atoms']}
    old = definitions['aurelian.head@3'].to_dict()['parameters']
    assert atoms['nose_plane'] == next(a for a in old['atoms'] if a['role'] == 'nose_plane')
    assert all(a['primitive'] == 'sphere' for a in head['atoms'] if a['role'] != 'nose_plane')
    assert not {'chin','lower_face','left_cheek_plane','right_cheek_plane','mouth_line'} & atoms.keys()
    assert atoms['brow_ridge']['dimensions'][1] < .38


def test_integrated_brow_and_visible_mouth_revision():
    definitions = catalog()
    head = definitions['aurelian.head@6']
    golden = json.loads((ROOT/'tests/fixtures/head-v6-golden.json').read_text())
    assert golden == {head.reference: head.sha256}
    parameters = head.to_dict()['parameters']
    atoms = {a['role']:a for a in parameters['atoms']}
    assert 'brow_ridge' not in atoms
    assert 'integrated_brow' in parameters['landmarks']
    assert parameters['operations'][-1] == dict(target='cranium', operand='mouth_line', operation='DIFFERENCE', solver='EXACT')
    assert atoms['mouth_line']['dimensions'][2] == .13
    assert atoms['mouth_line']['location'][2] < atoms['nose_plane']['location'][2]-atoms['nose_plane']['depth']/2


def test_rounded_nose_and_lower_brim_revisions():
    definitions = catalog()
    for filename in ('head-v7-golden.json', 'head-v8-golden.json', 'helmet-v2-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/filename).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    head = definitions['aurelian.head@8'].to_dict()['parameters']
    atoms = {a['role']: a for a in head['atoms']}
    previous = definitions['aurelian.head@6'].to_dict()['parameters']
    for atom in previous['atoms']:
        if not atom['role'].startswith('nose_'):
            assert atoms[atom['role']] == atom
    assert atoms['nose_bridge']['primitive'] == 'sphere'
    assert 'nose_plane' not in atoms and 'nose_root' not in atoms
    rigid_matrix(atoms['nose_bridge']['frame_mm'])
    old = definitions['aurelian.helmet@1'].to_dict()['parameters']['atoms']
    new = definitions['aurelian.helmet@2'].to_dict()['parameters']['atoms']
    for before, after in zip(old, new):
        if before['role'] != 'helmet_face_opening':
            assert before == after
            continue
        assert after['location'][2]-after['dimensions'][2]/2 == pytest.approx(before['location'][2]-before['dimensions'][2]/2)
        assert after['location'][2]+after['dimensions'][2]/2 == pytest.approx(before['location'][2]+before['dimensions'][2]/2-.22)
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for ref in ('aurelian.head@12', 'aurelian.helmet@5'):
        assert sum(p['part'] == ref for p in assembly['placements']) == 5


def test_full_length_mail_skirt_revision():
    definitions = catalog()
    skirt = definitions['aurelian.skirt@3']
    golden = json.loads((ROOT/'tests/fixtures/skirt-v3-golden.json').read_text())
    assert golden == {skirt.reference: skirt.sha256}
    p = skirt.to_dict()['parameters']
    assert p['landmarks']['hem'][2] == -4.85
    assert len(p['operations']) == 13*30
    assert all(o['solver'] == 'EXACT' for o in p['operations'])
    centers = p['chainmail']['centers_local']
    front = [c for c in centers if c[1] < -.5]
    assert min(c[2] for c in front) < -4.6
    assert max(c[2] for c in front) > -.8
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    assert sum(p['part'] == skirt.reference for p in assembly['placements']) == 5


def test_cape_revisions_remove_only_skirt_columns():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/capes-v2-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    removed = {'cape_left_sweep', 'cape_right_sweep'}
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for ref in golden:
        previous = definitions[ref.replace('@2', '@1')].to_dict()['parameters']
        current = definitions[ref].to_dict()['parameters']
        assert current['atoms'] == [a for a in previous['atoms'] if a['role'] not in removed]
        assert current['operations'] == previous['operations']
        assert not removed.intersection(definitions[ref].output_roles)
        assert sum(p['part'] == ref for p in assembly['placements']) == 1


def test_contoured_face_revisions_preserve_nose_and_mouth():
    definitions = catalog()
    for revision in (9, 10, 11):
        head = definitions[f'aurelian.head@{revision}']
        golden = json.loads((ROOT/f'tests/fixtures/head-v{revision}-golden.json').read_text())
        assert golden == {head.reference: head.sha256}
        p = head.to_dict()['parameters']
        atoms = {a['role']: a for a in p['atoms']}
        old = {a['role']: a for a in definitions['aurelian.head@8'].to_dict()['parameters']['atoms']}
        assert atoms['nose_bridge'] == old['nose_bridge']
        assert atoms['mouth_line'] == old['mouth_line']
        assert 'brow_ridge' not in atoms
        assert head.output_roles == ('cranium',)
        for side in ('left', 'right'):
            rigid_matrix(atoms[f'{side}_eye_socket']['frame_mm'])
            assert any(o['operand'] == f'{side}_cheek_hollow' and o['operation'] == 'DIFFERENCE' for o in p['operations'])
        assert p['operations'][-1]['operand'] == 'mouth_line'


def test_inward_nose_and_shield_hand_revisions():
    definitions = catalog()
    for filename in ('head-v12-golden.json', 'shield-arms-v2-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/filename).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    before = {a['role']:a for a in definitions['aurelian.head@11'].to_dict()['parameters']['atoms']}
    after = {a['role']:a for a in definitions['aurelian.head@12'].to_dict()['parameters']['atoms']}
    for role in before:
        if role != 'nose_bridge':
            assert before[role] == after[role]
    old, new = before['nose_bridge'], after['nose_bridge']
    assert old['dimensions'] == new['dimensions']
    half = new['dimensions'][2]/2
    for axis in range(3):
        assert old['frame_mm'][axis][3]+old['frame_mm'][axis][2]*half == pytest.approx(new['frame_mm'][axis][3]+new['frame_mm'][axis][2]*half)
    assert new['frame_mm'][1][3]-new['frame_mm'][1][2]*half > old['frame_mm'][1][3]-old['frame_mm'][1][2]*half+.3
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for suffix in ('', '-b', '-c', '-d', '-e'):
        ref = f'aurelian.left-arm{suffix}@2'
        assert sum(p['part'] == ref.replace('@2','@3') for p in assembly['placements']) == 1
        previous = definitions[ref.replace('@2','@1')].to_dict()['parameters']['atoms']
        current = definitions[ref].to_dict()['parameters']['atoms']
        for old_atom,new_atom in zip(previous,current):
            if old_atom['role'] not in {'left_palm','left_grouped_fingers','left_thumb','left_cuff'}:
                assert old_atom == new_atom


def test_equipment_revisions_remove_shield_ground_cones():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/equipment-joins-v2-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for ref in golden:
        before = definitions[ref.replace('@2', '@1')].to_dict()['parameters']
        after = definitions[ref].to_dict()['parameters']
        assert after['atoms'] == [a for a in before['atoms'] if a['role'] != 'shield_ground_heel']
        assert after['operations'] == before['operations']
        assert definitions[ref].output_roles == ('shield_spear_brace',)
        assert sum(p['part'] == ref for p in assembly['placements']) == 1


def test_rounded_projecting_boot_revisions():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/boots-v2-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for ref in golden:
        before = definitions[ref.replace('@2', '@1')].to_dict()['parameters']['atoms']
        after = definitions[ref].to_dict()['parameters']['atoms']
        for old,new in zip(before,after):
            if new['role'].endswith('_toe'):
                assert new['primitive'] == 'sphere'
                assert new['location'][1]-new['dimensions'][1]/2 < old['location'][1]-old['dimensions'][1]/2-.5
            elif new['role'].endswith('_sole'):
                assert new['location'][1]+new['dimensions'][1]/2 == pytest.approx(old['location'][1]+old['dimensions'][1]/2)
                assert new['bevel'] > old['bevel']
            else:
                assert new == old
        assert sum(p['part'] == ref.replace('@2', '@4') for p in assembly['placements']) == 1


def test_shaped_boot_revisions():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/boots-v3-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    for ref in golden:
        p = definitions[ref].to_dict()['parameters']
        side = 'left' if 'left-leg' in ref else 'right'
        atoms = {a['role']:a for a in p['atoms']}
        assert atoms[side+'_toe']['primitive'] == 'cube'
        assert atoms[side+'_toe']['bevel'] >= .2
        assert atoms[side+'_ankle']['primitive'] == 'cone'
        assert any(o['operation'] == 'UNION' and o['operand'] == side+'_boot_instep' for o in p['operations'])
        assert p['operations'][-1]['operand'] == side+'_sole_arch'
        assert sum(placement['part'] == ref.replace('@3','@4') for placement in assembly['placements']) == 1


def test_cloth_waist_wrap_shared_recipe():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/cloth-waist-wrap-v1-golden.json').read_text())
    assert golden == {ref:definitions[ref].sha256 for ref in golden}
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    wraps = [p for p in assembly['placements'] if p['part']=='aurelian.cloth-waist-wrap@1']
    assert len(wraps)==5
    for wrap in wraps:
        plate = next(p for p in assembly['placements'] if p['instance_id']==wrap['instance_id'].replace('/waist-wrap','/mail'))
        assert wrap['mount']==plate['mount']


def test_central_breastplate_pleat():
    definitions = catalog()
    plate = definitions['aurelian.chest-plate@3']
    golden = json.loads((ROOT/'tests/fixtures/chest-plate-v3-golden.json').read_text())
    assert golden == {plate.reference:plate.sha256}
    p = plate.to_dict()['parameters']
    before = definitions['aurelian.chest-plate@2'].to_dict()['parameters']
    assert p['atoms'][:len(before['atoms'])] == before['atoms']
    assert p['operations'][2:] == before['operations']
    assert p['landmarks']['central_pleat'][0] == 0
    assert p['operations'][1]['operation'] == 'UNION'
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    assert sum(a['part'] == 'aurelian.chest-plate@4' for a in assembly['placements']) == 5


def test_shallow_pleat_revision():
    definitions = catalog()
    plate = definitions['aurelian.chest-plate@4']
    golden = json.loads((ROOT/'tests/fixtures/chest-plate-v4-golden.json').read_text())
    assert golden == {plate.reference:plate.sha256}
    before = definitions['aurelian.chest-plate@3'].to_dict()['parameters']
    after = plate.to_dict()['parameters']
    assert before['operations'] == after['operations']
    for old,new in zip(before['atoms'],after['atoms']):
        if old['role']=='central_pleat':
            assert new['location'][1]>old['location'][1]
        elif old['role']=='pleat_contour':
            assert new['dimensions'][1]<old['dimensions'][1]
        else:
            assert old==new


def test_grass_base_revision_preserves_strip():
    definitions = catalog()
    base = definitions['aurelian.strip@2']
    golden = json.loads((ROOT/'tests/fixtures/grass-strip-v2-golden.json').read_text())
    assert golden == {base.reference:base.sha256}
    p = base.to_dict()['parameters']
    assert p['atoms'][0] == definitions['aurelian.strip@1'].to_dict()['parameters']['atoms'][0]
    assert p['texture']['seed'] == 1001
    assert len(p['atoms']) > 400
    for blade in p['atoms'][1:]:
        assert abs(blade['location'][0])+.2 < 10
        assert abs(blade['location'][1])+.2 < 2.5
        assert blade['location'][2]-blade['depth']/2 < 1
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    assert assembly['placements'][0]['part'] == 'aurelian.base-body-20x5@1'


def test_rounded_ground_texture():
    definitions = catalog()
    base = definitions['aurelian.strip@3']
    golden = json.loads((ROOT/'tests/fixtures/ground-strip-v3-golden.json').read_text())
    assert golden == {base.reference:base.sha256}
    p = base.to_dict()['parameters']
    assert p['atoms'][0] == definitions['aurelian.strip@1'].to_dict()['parameters']['atoms'][0]
    assert len(p['atoms']) == 421
    for bump in p['atoms'][1:]:
        assert bump['primitive'] == 'sphere'
        assert bump['location'][2]-bump['dimensions'][2]/2 < 1
        assert bump['location'][2]+bump['dimensions'][2]/2 <= 1.12
        assert abs(bump['location'][0])+bump['dimensions'][0]/2 < 10
        assert abs(bump['location'][1])+bump['dimensions'][1]/2 < 2.5


def test_noise_ground_is_one_continuous_component():
    definitions = catalog()
    base = definitions['aurelian.strip@4']
    golden = json.loads((ROOT/'tests/fixtures/noise-strip-v4-golden.json').read_text())
    assert golden == {base.reference:base.sha256}
    assert base.output_roles == ('strip',)
    p = base.to_dict()['parameters']
    assert len(p['operations']) == 257
    assert all(o['operation']=='UNION' for o in p['operations'][:-1])
    assert p['operations'][-1]['operand']=='strip_boundary'
    assert len({a['location'][2] for a in p['atoms'][1:-1]}) > 200
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    assert assembly['placements'][0]['part']=='aurelian.base-body-20x5@1'


def test_shield_torso_connectors_overlap_both_attachments():
    from fdm_sculpt.components.parts import inverse_rigid
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/shield-torso-connectors-v1-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()), definitions)
    placements = {p['instance_id']:p for p in assembly['placements']}
    for i in range(1,6):
        prefix = f'elf-{i:02d}/'
        connector = placements[prefix+'shield-torso-connector']
        atom = definitions[connector['part']].to_dict()['parameters']['atoms'][0]
        assert atom['radius'] == .46
        assert connector['mount'] == placements[prefix+'torso']['mount']
        f = multiply(inverse_rigid(placements[prefix+'shield']['mount']), connector['mount'])
        start = [sum(f[j][k]*atom['start'][k] for k in range(3))+f[j][3] for j in range(3)]
        assert start == pytest.approx([0,.30,1.30], abs=1e-7)
        # Endpoint is inside the shield thickness; torso endpoint is inside its ellipsoid.
        assert -.52 < start[1] < .52
        x,y,z = atom['end']
        assert (x/.92)**2+((y-.06)/.65)**2+(z/1.09)**2 < 1


def test_arms_reach_shield_backs():
    from fdm_sculpt.components.parts import inverse_rigid
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/shield-arms-v3-golden.json').read_text())
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()),definitions)
    placements = {p['instance_id']:p for p in assembly['placements']}
    for i in range(1,6):
        prefix = f'elf-{i:02d}/'
        arm,shield = placements[prefix+'left-arm'],placements[prefix+'shield']
        assert arm['part'] in golden
        p = definitions[arm['part']].to_dict()['parameters']
        atoms = {a['role']:a for a in p['atoms']}
        finger = atoms['left_grouped_fingers']
        f = multiply(multiply(inverse_rigid(shield['mount']),arm['mount']),finger['frame_mm'])
        center_y = sum(f[1][j]*finger['location'][j] for j in range(3))+f[1][3]
        front_y = center_y-sum(abs(f[1][j])*finger['dimensions'][j]/2 for j in range(3))
        assert front_y == pytest.approx(.50,abs=1e-7)
        assert atoms['left_forearm']['start'] == p['landmarks']['left_elbow']
        assert atoms['left_forearm']['end'] == p['landmarks']['left_cuff']


def test_lower_shield_attachments():
    from fdm_sculpt.components.parts import inverse_rigid
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/shield-lower-connectors-v1-golden.json').read_text())
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()),definitions)
    placements = {p['instance_id']:p for p in assembly['placements']}
    for i in range(1,6):
        prefix = f'elf-{i:02d}/'
        attachment = placements[prefix+'shield-lower-connector']
        assert attachment['part'] in golden
        assert attachment['mount'] == placements[prefix+'skirt']['mount']
        atom = definitions[attachment['part']].to_dict()['parameters']['atoms'][0]
        assert atom['radius'] == .42
        f = multiply(inverse_rigid(placements[prefix+'shield']['mount']),attachment['mount'])
        start = [sum(f[j][k]*atom['start'][k] for k in range(3))+f[j][3] for j in range(3)]
        assert start == pytest.approx([0,.30,-1.45],abs=1e-7)
        x,y,z = atom['end']
        assert -4.85 < z < -.5
        radius = 1.55-(z+4.85)*.58/4.35
        assert (x/radius)**2+(y/(.75*radius))**2 < 1


def test_rounded_triangle_crest_revision():
    definitions = catalog()
    crest = definitions['aurelian.crest@3']
    golden = json.loads((ROOT/'tests/fixtures/crest-v3-golden.json').read_text())
    assert golden == {crest.reference:crest.sha256}
    p = crest.to_dict()['parameters']
    atoms = {a['role']:a for a in p['atoms']}
    mask = atoms['helmet_leaf_crest_outline']
    assert mask['primitive']=='cone' and mask['radius1']>mask['radius2']
    assert mask['bevel']>.0
    assert mask['location'][0]==atoms['helmet_crest_spine_outline']['location'][0]==0
    assert p['operations'][-1] == dict(target='helmet_crest_spine',operand='helmet_leaf_crest_outline',operation='INTERSECT',solver='EXACT')
    assembly = resolve_assembly(json.loads((ROOT/'specs/elf-modular-visual.json').read_text()),definitions)
    assert sum(a['part']=='aurelian.crest@4' for a in assembly['placements'])==5


def test_soft_crest_with_tapered_underside():
    definitions = catalog()
    crest = definitions['aurelian.crest@4']
    golden = json.loads((ROOT/'tests/fixtures/crest-v4-golden.json').read_text())
    assert golden == {crest.reference:crest.sha256}
    p = crest.to_dict()['parameters']
    atoms = {a['role']:a for a in p['atoms']}
    assert atoms['helmet_leaf_crest_outline']['bevel']==.14
    rigid_matrix(atoms['crest_lower_taper']['frame_mm'])
    assert p['landmarks']['lower_taper_front'][2] > p['landmarks']['lower_taper_start'][2]
    for role in crest.output_roles:
        assert [o for o in p['operations'] if o['target']==role][-1]['operand']=='crest_lower_taper'


@pytest.mark.integration
def test_saved_modular_provenance():
    output = os.environ.get('PARTS_PROOF_BUILD')
    if not output:
        pytest.skip('set PARTS_PROOF_BUILD to a modular visual assembly')
    output = Path(output)
    assert json.loads((output/'saved-provenance.json').read_text())['passes']
    review = json.loads((output/'visual-review.json').read_text())
    assert review['placements'] == 102 and review['digitally_validated'] is False
    assert len(review['reused_parts']) + len(review['compiled_parts']) == 54
