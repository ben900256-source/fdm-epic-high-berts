"""Pinned horse anatomy, rider attachment and saved visual-review contracts."""
import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentDefinition
from fdm_sculpt.components.parts import resolve_assembly, rigid_matrix
from fdm_sculpt.components.refined_horse import (
    HORSE_REFERENCE, BARDING_REFERENCE, apply, refined_steed, refined_steed_v7,
    fitted_barding, fitted_barding_v10,
)

ROOT = Path(__file__).resolve().parents[1]


class Definitions(dict):
    def __missing__(self, ref):
        self[ref] = ComponentDefinition.from_dict(json.loads(
            (ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text()))
        return self[ref]


def test_recipes_resolve_to_immutable_goldens():
    definitions = Definitions()
    golden = json.loads((ROOT/'tests/fixtures/refined-horse-golden.json').read_text())
    parts = [refined_steed(1001), refined_steed_v7(1001),
             fitted_barding(definitions, 1001), fitted_barding_v10(definitions, 1001)]
    assert {p.reference:p.sha256 for p in parts} == golden
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    assert refined_steed_v7(1001).sha256 == golden[HORSE_REFERENCE]
    # Historical geometry is still pinned; no in-place edits to the old horse.
    old = json.loads((ROOT/'tests/fixtures/dragon-prince-heroic-steed-golden.json').read_text())
    assert {ref:definitions[ref].sha256 for ref in old} == old


def test_four_planted_hooves_stay_inside_cavalry_base():
    p = refined_steed_v7(1001).to_dict()['parameters']
    hooves = [a for a in p['atoms'] if a['role'].endswith('_hoof')]
    assert len(hooves) == 4
    for a in hooves:
        x, y, z = a['location']
        assert z-a['depth']/2 == pytest.approx(0)
        assert abs(x)+a['radius1']*a['scale'][0] < 3
        assert abs(y)+a['radius1']*a['scale'][1] < 6
        assert a['radius1']*2 >= 1.18
    points = p['landmarks']
    assert abs(points['-1_fore_ground'][1]-points['1_fore_ground'][1]) == pytest.approx(.60)
    assert abs(points['-1_hind_ground'][1]-points['1_hind_ground'][1]) == pytest.approx(.56)
    for tag, nodes in p['leg_paths'].items():
        assert min(radius*2 for _, radius in nodes) >= .86
        assert nodes[-1][0][:2] == points[tag+'_ground'][:2]
        if 'hind' in tag:
            assert nodes[1][0][1] < nodes[2][0][1]  # Stifle ahead of the hock.


def test_saddle_mount_and_rider_placements_stay_fixed():
    definitions = Definitions()
    old = definitions['aurelian.dragon-prince-horse@5'].to_dict()['parameters']['landmarks']
    new = definitions[HORSE_REFERENCE].to_dict()['parameters']['landmarks']
    for key in ('mount', 'ground', 'saddle', 'muzzle'):
        assert new[key] == old[key]
    assembly = json.loads((ROOT/'specs/elf-dragon-prince.json').read_text())
    resolved = resolve_assembly(assembly, definitions)
    placements = {p['instance_id']:p for p in resolved['placements']}
    assert placements['prince-01/horse']['part'] == HORSE_REFERENCE
    assert placements['prince-01/barding']['part'] == BARDING_REFERENCE
    historical = json.loads((ROOT/'specs/accepted-army-sources.json').read_text())['sources']['specs/elf-dragon-prince.json']
    for previous in historical['placements']:
        # Shield orientation was deliberately changed in the accepted infantry update.
        if previous['instance_id'].endswith('/shield'):continue
        assert placements[previous['instance_id']]['mount'] == previous['mount']


def test_refinement_uses_owned_primitives_and_ordered_exact_csg():
    p = refined_steed_v7(1001).to_dict()['parameters']
    roles = {a['role'] for a in p['atoms']}
    assert len(roles) == len(p['atoms'])
    assert [a['role'] for a in p['atoms'] if a['export']] == ['barrel']
    for atom in p['atoms']:
        assert atom['primitive'] in {'sphere', 'cone', 'cube'}
        if 'frame_mm' in atom:rigid_matrix(atom['frame_mm'])
    for op in p['operations']:
        assert op['target'] in roles and op['operand'] in roles
        assert op['solver']=='EXACT'
    cuts = {op['operand'] for op in p['operations'] if op['operation']=='DIFFERENCE'}
    assert {'eye_socket_-1', 'eye_socket_1', 'nostril_-1', 'nostril_1', 'lip_seam'}.issubset(cuts)
    assert 'mouth_line' not in roles
    assert not any(role.startswith('mane_groove_') for role in roles)


@pytest.mark.parametrize('seed', [None, True, 1.5, '1001'])
def test_explicit_integer_seed_required(seed):
    with pytest.raises(ValueError):refined_steed_v7(seed)


def test_replacement_is_idempotent_and_does_not_move_other_parts():
    source = json.loads((ROOT/'specs/accepted-army-sources.json').read_text())['sources']['specs/elf-dragon-prince.json']
    before = deepcopy(source)
    definitions = Definitions()
    apply(source, definitions)
    for a, b in zip(before['placements'], source['placements']):
        assert a['mount']==b['mount']
        if a['instance_id'].split('/')[-1] not in {'horse', 'barding'}:assert a==b
    once = deepcopy(source)
    apply(source, definitions)
    assert source==once


@pytest.mark.integration
def test_saved_refined_horse_provenance_and_cache_reuse():
    folder = os.environ.get('REFINED_HORSE_REVIEW')
    if not folder:pytest.skip('set REFINED_HORSE_REVIEW for the saved visual review')
    folder = Path(folder)
    for name in ('horse', 'assembled'):
        saved = json.loads((folder/name/'saved-provenance.json').read_text())
        assert saved['passes'] and all(saved['checks'].values())
        review = json.loads((folder/name/'visual-review.json').read_text())
        assert review['mode']=='modular-visual-preview' and not review['digitally_validated']
    horse = json.loads((folder/'horse/visual-review.json').read_text())
    assembly = json.loads((folder/'assembled/visual-review.json').read_text())
    assert horse['compiled_parts']==[HORSE_REFERENCE]
    assert assembly['compiled_parts']==[BARDING_REFERENCE]
    assert len(assembly['reused_parts'])==16 and HORSE_REFERENCE in assembly['reused_parts']
    job = json.loads((folder/'assembled/assembly-job.json').read_text())
    spec = json.loads((ROOT/'specs/elf-dragon-prince.json').read_text())
    assert job['assembly']['placements']==spec['placements']

    clearance = json.loads((folder/'assembled/reins-clearance.json').read_text())
    assert clearance['passes'] and not clearance['collisions']
    assert clearance['intended_grip_contact']['fist_dimensions_mm']==[1.25, 1.1875, 1.3125]
    assert clearance['intended_grip_contact']['samples']
