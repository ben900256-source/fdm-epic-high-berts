"""Artillery support geometry contracts; actual sliced gates remain separate."""
import json
import math
from pathlib import Path
import pytest
from fdm_sculpt.components.army_expansion import all_parts
from fdm_sculpt.components.artillery_print_fixes import engine_v3, crew_arms_v4, grounded_bolt
from fdm_sculpt.components.elves_v2 import point

ROOT=Path(__file__).resolve().parents[1]

def read(ref):
    return json.loads((ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text())['parameters']


def test_support_revisions_preserve_bow_and_loaded_bolt_geometry():
    original=read('aurelian.expansion-bolt-thrower@1');current=engine_v3(1001).to_dict()['parameters']
    a={v['role']:v for v in original['atoms']};b={v['role']:v for v in current['atoms']}
    preserved=[r for r in a if r!='elevation_screw']
    assert all(a[r]==b[r] for r in preserved)
    assert b['elevation_screw']['start'][2]<0
    assert original['landmarks']==current['landmarks']


def test_native_triangular_braces_start_in_base_and_grow_steeply():
    p=engine_v3(1001).to_dict()['parameters']
    for a in p['atoms']:
        if not a['role'].startswith(('bow_brace_','string_brace_')) or a['primitive']!='cone' or not a['export']:continue
        sx,sy,_=a['scale'];m=a['frame_mm']
        root=point(m,[0,sy,0])
        assert root[2]<0
        assert a['depth']>=.75
        for side in (-1,1):
            top=point(m,[side*math.sqrt(3)/2*sx,-sy/2,0])
            assert math.dist(root[:2],top[:2])<top[2]-root[2]


def test_loader_bolt_is_grounded_and_centered_in_existing_hand():
    p=grounded_bolt(1001).to_dict()['parameters'];grip=p['landmarks']['grip'];bottom=p['landmarks']['shaft_bottom']
    shaft=next(a for a in p['atoms'] if a['role']=='spare_bolt')
    axis=[b-a for a,b in zip(shaft['start'],shaft['end'])];length=math.sqrt(sum(v*v for v in axis));axis=[v/length for v in axis]
    distance=sum((g-b)*u for g,b,u in zip(grip,bottom,axis))
    assert [bottom[i]+axis[i]*distance for i in range(3)]==pytest.approx(grip)
    assert bottom[2]+6.4<1.2
    assert math.degrees(math.acos(axis[2]))>=6
    assert p['shaft_diameter_mm']>=1.0
    assert grip==crew_arms_v4(1001).to_dict()['parameters']['landmarks']['right_grip']


def test_crew_sleeve_roots_are_inside_the_original_leg_axes():
    p=crew_arms_v4(1001).to_dict()['parameters']
    old=read('aurelian.expansion-crew-arms@2')
    assert p['landmarks']==old['landmarks']
    for side,name in ((-1,'left'),(1,'right')):
        root=next(a for a in p['atoms'] if a['role']==f'sleeve_return_{side}_node_0')
        ankle=read(f'aurelian.{name}-leg-c@6')['landmarks'][name+'_ankle']
        assert root['location']==pytest.approx(ankle)
        assert max(root['dimensions'])<=.86


def test_supported_parts_are_used_only_in_artillery():
    refs={p.reference for p in all_parts(1001) if p.family.startswith('army-expansion-artillery-')}
    for file in (ROOT/'specs/army-expansion').glob('*.json'):
        placements=json.loads(file.read_text())['placements']
        if file.stem=='bolt-thrower':
            slots={p['instance_id']:p for p in placements}
            assert slots['engine']['part']=='aurelian.expansion-bolt-thrower@3'
            assert len([p for p in placements if p['part']=='aurelian.expansion-artillery-boot-seats@1'])==2
        else:
            assert not any(p['part'] in refs for p in placements)
