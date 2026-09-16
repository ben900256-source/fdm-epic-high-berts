import json
import os
from pathlib import Path
import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.components.parts import catalog, resolve_assembly
from fdm_sculpt.components.spearman_overhangs import revised_parts, refined_parts, sleeve_part, deposited_shield_part

ROOT = Path(__file__).resolve().parents[1]


def test_underside_revisions_match_goldens_and_resolve():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/spearman-overhangs-v1-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in revised_parts(definitions, 1001)} == golden
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    source = json.loads((ROOT/'specs/elf-modular-visual.json').read_text())
    assembly = resolve_assembly(source, definitions)
    refs = {p['part'] for p in assembly['placements']}
    refined = json.loads((ROOT/'tests/fixtures/spearman-overhangs-v2-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in refined_parts(definitions, 1001)} == refined
    assert {ref:definitions[ref].sha256 for ref in refined} == refined
    superseded = {p.to_dict()['parameters']['overhang_revision']['source'] for p in refined_parts(definitions, 1001)}
    assert (set(golden)-superseded-{'aurelian.torso@3'}) | (set(refined)-{'aurelian.shield@4'}) <= refs
    sleeve_golden = json.loads((ROOT/'tests/fixtures/spearman-overhang-sleeve-golden.json').read_text())
    sleeve = sleeve_part(definitions, 1001)
    assert {sleeve.reference:sleeve.sha256} == sleeve_golden
    assert sleeve.reference in refs and definitions[sleeve.reference].sha256 == sleeve.sha256
    shield_golden = json.loads((ROOT/'tests/fixtures/spearman-overhang-shield-v5-golden.json').read_text())
    shield = deposited_shield_part(definitions, 1001)
    assert {shield.reference:shield.sha256} == shield_golden
    assert definitions[shield.reference].sha256 == shield.sha256
    assert 'aurelian.shield@2' in refs and shield.reference not in refs
    for path in sorted((ROOT/'specs/models/spearmen').glob('*.json')):
        assert load_model(path, definitions)['placements']
    study = load_assembly(ROOT/'specs/elf-spearmen-overhang-study.json', definitions)
    assert len(study['placements']) == 105
    assert next(p['part'] for p in study['placements'] if p['instance_id']=='strip') == 'aurelian.base-body-20x5-plain@1'


def test_approved_face_and_helmet_and_spear_grip_are_preserved():
    definitions = catalog()
    assembly = json.loads((ROOT/'specs/elf-modular-visual.json').read_text())
    for slot, reference in [('head','aurelian.head@12'), ('helmet','aurelian.helmet@7'), ('crest','aurelian.crest@4')]:
        assert {p['part'] for p in assembly['placements'] if p['instance_id'].endswith('/'+slot)} == {reference}
    old = definitions['aurelian.spear@3'].to_dict()['parameters']
    new = definitions['aurelian.spear@4'].to_dict()['parameters']
    assert old['atoms'][0] == new['atoms'][0]
    assert old['atoms'][2] == new['atoms'][2]
    lower, upper = new['atoms'][1:3]
    assert lower['scale'][1] == upper['scale'][1]
    assert lower['radius2'] == upper['radius1']
    assert lower['location'][2]+lower['depth']/2 > upper['location'][2]-upper['depth']/2
    assert (lower['radius2']-lower['radius1'])/lower['depth'] < 1


def test_new_ramps_keep_original_geometry_and_landmarks():
    definitions = catalog()
    for part in revised_parts(definitions, 1001):
        new = part.to_dict()['parameters']
        old = definitions[new['overhang_revision']['source']].to_dict()['parameters']
        assert new['landmarks'] == old['landmarks']
        assert new['operations'] == old['operations']
        if part.component_id != 'aurelian.spear':
            assert new['atoms'][:len(old['atoms'])] == old['atoms']
            assert len(new['atoms']) > len(old['atoms'])


@pytest.mark.integration
def test_saved_overhang_scene_provenance():
    output = os.environ.get('OVERHANG_PROOF_BUILD')
    if not output:
        pytest.skip('set OVERHANG_PROOF_BUILD to the saved underside study')
    output = Path(output)
    proof = json.loads((output/'saved-provenance.json').read_text())
    assert proof['passes'] and proof['checks']['visual_only'] and proof['checks']['hidden_sources']
    job = json.loads((output/'assembly-job.json').read_text())
    assert job['assembly'] == load_assembly(ROOT/'specs/elf-spearmen-overhang-study.json')
    for placement in job['assembly']['placements']:
        assert proof['checks'][placement['part']]
        assert proof['checks'][placement['instance_id']]
