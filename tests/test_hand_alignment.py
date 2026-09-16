"""Grip alignment, unchanged sleeves, and pinned hand-only rotations."""
import json
from pathlib import Path
import pytest

from fdm_sculpt.army import load_model
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.elves_v2 import identity
from fdm_sculpt.components.hand_alignment import revised_parts, direction
from fdm_sculpt.components.robe_arms import hand_atom
from fdm_sculpt.workshop import models

ROOT=Path(__file__).resolve().parents[1]


def test_aligned_hands_preserve_sleeves_and_golden_revisions():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/hand-alignment-sources.json').read_text())
    golden=json.loads((ROOT/'tests/fixtures/hand-alignment-golden.json').read_text())
    for _ in range(2):
        parts=revised_parts(definitions,manifest,1001)
        assert {p.reference:p.sha256 for p in parts}==golden
    assert {ref:definitions[ref].sha256 for ref in golden}==golden
    for part in parts:
        p=part.to_dict()['parameters']
        before=definitions[p['hand_alignment_source']].to_dict()['parameters']
        assert p['cloth_pose']==before['cloth_pose']
        assert p['operations']==before['operations']
        for a,b in zip(p['atoms'],before['atoms']):
            if not hand_atom(a):assert a==b
            else:assert {k:v for k,v in a.items() if k!='frame_mm'}=={k:v for k,v in b.items() if k!='frame_mm'}


def test_live_model_grip_axes_match_the_held_items():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/hand-alignment-sources.json').read_text())
    by_model={m['id']:m for m in models()}
    # Audit records predate the workshop's unit-type split; recipes are shared.
    by_model.update({m['id'].replace('swordsmen/','spearmen/'):m
                     for m in models() if m['family']=='swordsmen'})
    resolved={}
    for check in manifest['audit']:
        model=check['model']
        if model not in resolved:
            resolved[model]={p['instance_id']:p for p in load_model(by_model[model]['path'],definitions)['placements']}
        placement=resolved[model][check['arm']]
        p=definitions[placement['part']].to_dict()['parameters']
        finger=next(a for a in p['atoms'] if 'fingers' in a['role'] and a['primitive']=='cube')
        axis=direction(finger.get('frame_mm',identity()),[0,0,1])
        assert abs(sum(a*b for a,b in zip(axis,check['target_axis'])))==pytest.approx(1,abs=1e-7),(model,check['arm'])
