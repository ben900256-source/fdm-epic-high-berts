"""Pinned poses, unchanged weapon grips and family coverage for cloth arms."""
from copy import deepcopy
import json
from pathlib import Path

from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.robe_arms import hand_atom, revised_parts, fitted_bow_shoulders
from fdm_sculpt.components.robe_elbows import revised_parts as elbow_parts
from fdm_sculpt.workshop import models

ROOT=Path(__file__).resolve().parents[1]


def test_pose_recipes_and_retained_hands():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/robe-arm-sources.json').read_text())
    golden=json.loads((ROOT/'tests/fixtures/robe-arms-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in revised_parts(definitions,manifest,1001)}==golden
    assert {ref:definitions[ref].sha256 for ref in golden}==golden
    assert len(golden)==32
    fitted=json.loads((ROOT/'tests/fixtures/robe-arm-shoulders-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in fitted_bow_shoulders(definitions,1001)}==fitted
    assert {ref:definitions[ref].sha256 for ref in fitted}==fitted
    golden.update(fitted)
    for ref in golden:
        current=definitions[ref].to_dict()['parameters']
        source=definitions[current['robe_source']].to_dict()['parameters']
        assert current['landmarks']==source['landmarks']
        expected=[]
        for atom in source['atoms']:
            if hand_atom(atom):
                atom=deepcopy(atom)
                atom['export']=True
                expected.append(atom)
        assert [a for a in current['atoms'] if hand_atom(a)]==expected
        assert not any('vambrace' in a['role'] or 'pauldron' in a['role'] or
                       a['role'].endswith('_upper_arm') for a in current['atoms'])


def test_every_spearman_and_archer_arm_uses_its_own_cloth_pose():
    definitions=catalog()
    golden=json.loads((ROOT/'tests/fixtures/robe-elbows-golden.json').read_text())
    golden.pop('aurelian.horn-arm@10')
    golden.update(json.loads((ROOT/'tests/fixtures/horn-palm-cleanup-golden.json').read_text()))
    used=set()
    for model in models():
        placements=load_model(model['path'],definitions)['placements']
        for p in placements:
            if model['family'] in ('spearmen','swordsmen','archers'):
                assert p['instance_id'] not in ('left-tunic','right-tunic')
                if p['instance_id'].endswith('-arm'):
                    params=definitions[p['part']].to_dict()['parameters']
                    source=params.get('hand_alignment_source',p['part'])
                    assert source in golden,(model['id'],p['part'])
                    used.add(source)
            elif p['instance_id'].endswith('-arm'):
                assert p['part'] not in golden
    assert used==set(golden)


def test_elbow_texture_keeps_the_reviewed_sleeves_and_hands():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/robe-elbow-sources.json').read_text())
    golden=json.loads((ROOT/'tests/fixtures/robe-elbows-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in elbow_parts(definitions,manifest,1001)}==golden
    assert {ref:definitions[ref].sha256 for ref in golden}==golden
    for ref in golden:
        p=definitions[ref].to_dict()['parameters']
        source=definitions[p['elbow_texture_source']].to_dict()['parameters']
        assert p['atoms'][:len(source['atoms'])]==source['atoms']
        assert p['operations'][:len(source['operations'])]==source['operations']
        assert p['landmarks']==source['landmarks']
        assert p['cloth_pose']==source['cloth_pose']
        assert definitions[ref].output_roles==definitions[p['elbow_texture_source']].output_roles
        added=p['atoms'][len(source['atoms']):]
        assert len(added)==26 and all(a['role'].startswith('elbow_cloth_') for a in added)
