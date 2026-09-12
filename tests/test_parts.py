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
    assert sum(p['part'] == crest.reference for p in assembly['placements']) == 5


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
    for ref in ('aurelian.chest-plate@2', 'aurelian.skirt@2'):
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
    for ref in ('aurelian.shield@2','aurelian.shield-insignia@2','aurelian.chest-plate@2',
                'aurelian.torso@2','aurelian.left-tunic@2','aurelian.right-tunic@2','aurelian.head@6'):
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


@pytest.mark.integration
def test_saved_modular_provenance():
    output = os.environ.get('PARTS_PROOF_BUILD')
    if not output:
        pytest.skip('set PARTS_PROOF_BUILD to a modular visual assembly')
    output = Path(output)
    assert json.loads((output/'saved-provenance.json').read_text())['passes']
    review = json.loads((output/'visual-review.json').read_text())
    assert review['placements'] == 86 and review['digitally_validated'] is False
    assert len(review['reused_parts']) + len(review['compiled_parts']) == 42
