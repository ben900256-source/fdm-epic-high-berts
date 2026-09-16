"""Pinned shield pose changes and concealed join revisions."""
import json
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_tuck import revised_parts, tucked_mount, recessed_join_mount
from fdm_sculpt.workshop import models

ROOT = Path(__file__).resolve().parents[1]


def test_shield_tuck_recipes_and_resolver():
    definitions = catalog()
    for source, golden in [('shield-tuck-v3-sources.json','shield-tuck-golden.json'),
                           ('shield-tuck-v4-sources.json','shield-tuck-v4-golden.json'),
                           ('shield-tuck-v5-sources.json','shield-tuck-v5-golden.json'),
                           ('shield-tuck-sources.json','shield-tuck-v6-golden.json')]:
        manifest = json.loads((ROOT/'specs'/source).read_text())
        hashes = json.loads((ROOT/'tests/fixtures'/golden).read_text())
        for _ in range(2):
            parts = revised_parts(definitions, manifest, 1001)
            assert {p.reference:p.sha256 for p in parts} == hashes
        assert {ref:definitions[ref].sha256 for ref in hashes} == hashes


def test_tucked_shields_keep_the_grip_and_matching_insignia():
    manifest = json.loads((ROOT/'specs/shield-tuck-sources.json').read_text())
    assembly = load_assembly(ROOT/'specs/elf-modular-visual.json')
    placements = {p['instance_id']:p for p in assembly['placements']}
    for pose in manifest['poses']:
        # The whole row was subsequently lowered 1 mm for its thinner base.
        for key in ('shield','insignia','skirt','connector'):
            pose[key]['mount'][2][3] -= 1
        shield = placements[pose['shield']['instance_id']]
        assert shield['part'] == pose['shield']['part']
        assert shield['definition_sha256'] == pose['shield']['definition_sha256']
        assert shield['mount'] == tucked_mount(pose)
        assert placements[pose['insignia']['instance_id']]['mount'] == shield['mount']
        pivot = pose['pivot_shield_mm']
        offset = pose['offset_shield_mm']
        assert point(shield['mount'], pivot) == pytest.approx(point(pose['shield']['mount'], [a+b for a,b in zip(pivot,offset)]), abs=1e-8)
        assert pose['angle_degrees'] == 3
        tip = [0,0,-2.275]
        assert point(shield['mount'],tip)[1] > point(pose['shield']['mount'],tip)[1]+.65
        assert placements[pose['skirt']['instance_id']] == pose['skirt']
        join = placements[pose['connector']['instance_id']]
        assert join['mount'] == recessed_join_mount(pose)
        before = point(pose['connector']['mount'],[0,0,0])
        after = point(join['mount'],[0,0,0])
        assert sum((a-b)**2 for a,b in zip(after,before))**.5 == pytest.approx(.10)


def test_all_live_shield_models_use_concealed_joins():
    definitions = catalog()
    used = set()
    for model in models():
        p = {p['instance_id']:p for p in load_model(model['path'],definitions)['placements']}
        if 'shield' not in p:
            assert 'shield-lower-connector' not in p
            continue
        join = definitions[p['shield-lower-connector']['part']]
        assert join.version == 6
        assert join.output_roles == ('concealed_hem_join',)
        used.add(join.reference)
        params = join.to_dict()['parameters']
        root = params['landmarks']['skirt_attachment']
        tip = params['landmarks']['shield_tip_front']
        assert root[2] < tip[2]
        assert root[2] == -5.0  # embedded in the existing hem, above its bottom
        assert params['design']['embedded_width_mm'] >= .75
        assert all(a['primitive'] == 'cube' for a in params['atoms'])
        assert len(params['operations']) == 4
    golden = json.loads((ROOT/'tests/fixtures/shield-tuck-v6-golden.json').read_text())
    assert used == set(golden)
