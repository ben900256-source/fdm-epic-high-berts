"""Contract checks for the first visual army expansion; no manufacturing claims."""
import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.components.army_expansion import all_parts,PREFIX
from fdm_sculpt.components.core import ComponentDefinition
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.components.parts import resolve_assembly,validate_part
ROOT=Path(__file__).resolve().parents[1]
class Definitions(dict):
    def __missing__(self,ref):
        self[ref]=validate_part(ComponentDefinition.from_dict(json.loads((ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text())))
        return self[ref]
def index():return json.loads((ROOT/'specs/army-expansion-index.json').read_text())
def assembly(name):return json.loads((ROOT/'specs/army-expansion'/f'{name}.json').read_text())
def test_generated_parts_match_pinned_definitions_and_goldens():
    golden=json.loads((ROOT/'tests/fixtures/army-expansion-golden.json').read_text())
    assert {p.reference:p.sha256 for p in all_parts(1001)}==golden
    defs=Definitions()
    assert {ref:defs[ref].sha256 for ref in golden}==golden
    for ref in golden:
        p=defs[ref].to_dict()['parameters']
        assert p['visual_only'] and p['export_scale']==1.3
        assert all(o['solver']=='EXACT' for o in p['operations'])
@pytest.mark.parametrize('seed',[True,None,1.5,'1001'])
def test_seed_is_explicit_integer(seed):
    with pytest.raises(ValueError):all_parts(seed)
def test_every_requested_unit_and_character_mount_resolves():
    data=index();defs=Definitions()
    assert set(data['coverage'])=={'reavers','chariots','giant-eagles','dragon-rider','elven-bolt-thrower','general','hero','mage'}
    roles={a['role'] for a in data['assemblies']}
    assert len(roles)==17
    assert {f'{kind}-on-{mount}' for kind in ('general','hero','mage') for mount in ('eagle','dragon','chariot')}<=roles
    for a in data['assemblies']:
        spec=json.loads((ROOT/a['path']).read_text());assert resolve_assembly(spec,defs)==spec
    assert not data['digitally_validated']
def test_reavers_reuse_bare_reviewed_horse_and_three_aim_directions():
    spec=assembly('reavers');items=spec['placements']
    horses=[p for p in items if p['instance_id'].endswith('/horse')]
    assert len(horses)==3 and {p['part'] for p in horses}=={'aurelian.dragon-prince-horse@7'}
    assert not any('barding' in p['part'] for p in items)
    bows=[p for p in items if p['instance_id'].endswith('/bow')]
    assert len({json.dumps(p['mount'][:3]) for p in bows})==3
    assert {p['part'] for p in items if p['instance_id'].endswith('/head')}=={'aurelian.readable-head-trial@5'}
def test_character_weapons_are_centered_in_their_shared_hand_landmarks():
    defs=Definitions()
    for a in index()['assemblies']:
        slots={p['instance_id']:p for p in json.loads((ROOT/a['path']).read_text())['placements']}
        for name,weapon in slots.items():
            if name.split('/')[-1] not in ('staff','sword'):continue
            prefix=name.rsplit('/',1)[0]
            arms=slots[prefix+'/arms'];grip=defs[arms['part']].to_dict()['parameters']['landmarks']['right_grip']
            assert point(arms['mount'],grip)==pytest.approx(point(weapon['mount'],[0,0,0]),abs=1e-7)
def test_each_mounted_character_uses_the_creatures_declared_saddle():
    defs=Definitions()
    for mount in ('eagle','dragon'):
        for kind in ('general','hero','mage'):
            slots={p['instance_id']:p for p in assembly(kind+'-on-'+mount)['placements']}
            creature=slots['creature'];anchor=defs[creature['part']].to_dict()['parameters']['landmarks']['saddle']
            seat=slots['rider/saddle-and-legs']
            assert point(creature['mount'],anchor)==pytest.approx(point(seat['mount'],[0,0,0]))
            torso_anchor=defs[seat['part']].to_dict()['parameters']['landmarks']['torso']
            assert point(seat['mount'],torso_anchor)==pytest.approx(point(slots['rider/torso']['mount'],[0,0,0]))
def test_chariot_keeps_two_horses_and_two_crew_in_each_configuration():
    for name in ('chariot','general-on-chariot','hero-on-chariot','mage-on-chariot'):
        items=assembly(name)['placements']
        assert len([p for p in items if p['instance_id'].endswith('/horse')])==2
        assert {p['instance_id'] for p in items if p['instance_id'].endswith('/head')}=={'driver/head','passenger/head'}
        assert len([p for p in items if p['part']=='aurelian.expansion-chariot@5'])==1
@pytest.mark.integration
def test_saved_reviews_preserve_provenance_and_remain_visual_only():
    path=os.environ.get('ARMY_EXPANSION_REVIEW')
    if not path:pytest.skip('Set ARMY_EXPANSION_REVIEW to the saved review directory')
    # Later directories override only the assemblies they rebuilt.
    roots=[Path(value) for value in path.split(os.pathsep)]
    entries=index()['assemblies']+[dict(path=index()['overview'])]
    for a in entries:
        folder=next((root/'assemblies'/Path(a['path']).stem for root in reversed(roots)
                     if (root/'assemblies'/Path(a['path']).stem).is_dir()),None)
        assert folder is not None,a['path']
        saved=json.loads((folder/'saved-provenance.json').read_text());assert saved['passes'] and all(saved['checks'].values())
        review=json.loads((folder/'visual-review.json').read_text());assert review['mode']=='modular-visual-preview' and not review['digitally_validated']
        job=json.loads((folder/'assembly-job.json').read_text());spec=json.loads((ROOT/a['path']).read_text())
        assert job['assembly']['placements']==spec['placements']
        assert not list(folder.glob('*.stl')) and not list(folder.glob('*.gcode'))

    from collections import Counter
    records=[record for root in roots for record in json.loads((root/'review-record.json').read_text())]
    compiled=Counter(ref for r in records for ref in r['compiled'])
    assert all(count==1 for count in compiled.values())


def test_dragon_wing_prisms_meet_the_body_root_using_blenders_native_triangle():
    from math import sqrt
    part=Definitions()['aurelian.expansion-dragon@3'].to_dict()['parameters']
    panels=[a for a in part['atoms'] if a['role'].startswith('membrane_')]
    assert len(panels)==6
    # Native Blender cone(vertices=3) has its apex on +Y, not +X.
    for panel in panels:
        side=int(panel['role'].split('_')[1])
        apex=point(panel['frame_mm'],[0,panel['scale'][1],0])
        assert apex==pytest.approx([side*1.42,.9,4.65])
        corners=[point(panel['frame_mm'],[x*panel['scale'][0],-.5*panel['scale'][1],0])
                 for x in (-sqrt(3)/2,sqrt(3)/2)]
        assert min(c[2] for c in corners)>apex[2]
        assert panel['depth']>=.75


def test_thick_chariot_reins_meet_both_hands_and_rise_steeply_from_the_horses():
    from math import hypot
    defs=Definitions()
    reference='aurelian.expansion-chariot-reins@2'
    parameters=defs[reference].to_dict()['parameters']
    assert parameters['nominal_diameter_mm']==pytest.approx(1.16)
    assert parameters['minimum_terminal_diameter_mm']>=1.0
    for stations in parameters['route_stations'].values():
        hand,rump=stations[0][0],stations[1][0]
        assert hand[2]-rump[2]>=hypot(hand[0]-rump[0],hand[1]-rump[1])
        assert min(2*radius for _,radius in stations)>=1.0
    for name in ('chariot','general-on-chariot','hero-on-chariot','mage-on-chariot'):
        slots={p['instance_id']:p for p in assembly(name)['placements']}
        rein=slots['reins'];arms=slots['driver/arms']
        assert rein['part']==reference
        grips=defs[arms['part']].to_dict()['parameters']['landmarks']
        for grip in ('right_grip','left_grip'):
            assert point(rein['mount'],parameters['landmarks'][grip])==pytest.approx(
                point(arms['mount'],grips[grip]),abs=1e-7)


def test_regular_chariot_spear_preserves_locked_shaft_and_meets_hand_and_deck():
    from math import acos, degrees, dist
    defs=Definitions()
    slots={p['instance_id']:p for p in assembly('chariot')['placements']}
    assert 'passenger/sword' not in slots
    spear=slots['passenger/spear'];arms=slots['passenger/arms']
    assert spear['part']=='aurelian.expansion-chariot-spear@2'
    current={a['role']:a for a in defs[spear['part']].to_dict()['parameters']['atoms']}
    old={a['role']:a for a in defs['aurelian.uniform-spear-140-trial@3'].to_dict()['parameters']['atoms']}
    assert current['spear']==old['spear']
    assert current['spear_leaf_tip']['radius2']>old['spear_leaf_tip']['radius2']
    landmarks=defs[spear['part']].to_dict()['parameters']['landmarks']
    bottom=point(spear['mount'],landmarks['shaft_bottom'])
    top=point(spear['mount'],landmarks['shaft_top'])
    axis=[(b-a)/dist(bottom,top) for a,b in zip(bottom,top)]
    assert degrees(acos(axis[2]))==pytest.approx(18)
    assert axis[0]>0 and axis[1]<0
    assert dist(bottom,top)==pytest.approx(13.35)  # No rescaling of the cache.
    grip=point(arms['mount'],defs[arms['part']].to_dict()['parameters']['landmarks']['right_grip'])
    along=sum((g-b)*u for g,b,u in zip(grip,bottom,axis))
    assert [bottom[i]+along*axis[i] for i in range(3)]==pytest.approx(grip,abs=1e-7)
    assert bottom[2]==pytest.approx(3.85)
    assert abs(bottom[0])+.7<2.75
    assert 1.1+.7<bottom[1]<6.5-.7
    for kind in ('general','hero','mage'):
        names={p['instance_id'] for p in assembly(kind+'-on-chariot')['placements']}
        assert 'passenger/spear' not in names
        assert 'passenger/'+('staff' if kind=='mage' else 'sword') in names


def test_chariot_underbody_is_grounded_and_wheels_have_continuous_stock():
    from math import sqrt
    defs=Definitions()
    current=defs['aurelian.expansion-chariot@2'].to_dict()['parameters']
    original=defs['aurelian.expansion-chariot@1'].to_dict()['parameters']
    atoms={a['role']:a for a in current['atoms']}
    old={a['role']:a for a in original['atoms']}
    assert atoms['deck']==old['deck']
    assert current['landmarks']==original['landmarks']
    hull=atoms['tapered_underbody']
    bottom=point(hull['frame_mm'],[0,0,-hull['depth']/2])
    top=point(hull['frame_mm'],[0,0,hull['depth']/2])
    assert bottom[2]<0
    assert top[2]>atoms['deck']['location'][2]-atoms['deck']['dimensions'][2]/2
    assert (hull['radius2']-hull['radius1'])/hull['depth']<1
    assert sqrt(2)*hull['radius2']>=max(atoms['deck']['dimensions'][:2])
    operations=current['operations']
    for side in (-1,1):
        web=atoms[f'wheel_web_{side}']
        assert web['depth']>=.75
        assert web['radius']>atoms[f'rim_hollow_{side}']['radius']
        union=next(i for i,o in enumerate(operations) if o['operand']==web['role'])
        cut=next(i for i,o in enumerate(operations) if o['operand']==f'rim_hollow_{side}')
        assert union>cut and operations[union]['operation']=='UNION'
        assert len([a for a in atoms if a.startswith(f'spoke_{side}_')])==8


def test_chariot_shield_braces_anchor_below_the_deck_and_preserve_shared_faces():
    defs=Definitions()
    ref='aurelian.expansion-chariot-shield-brace@1'
    parameters=defs[ref].to_dict()['parameters']
    assert parameters['minimum_square_section_mm']>=1.0
    foot=next(a for a in parameters['atoms'] if a['role']=='shield_brace_foot')
    for name in ('chariot','general-on-chariot','hero-on-chariot'):
        slots={p['instance_id']:p for p in assembly(name)['placements']}
        brace=slots['passenger/shield-brace'];shield=slots['passenger/shield']
        assert brace['part']==ref and brace['mount']==shield['mount']
        assert shield['part']=='aurelian.shield@6'
        assert slots['passenger/shield-insignia']['part']=='aurelian.readable-insignia-trial@6'
        root=point(brace['mount'],parameters['landmarks']['cart_root'])
        assert root[2]-foot['dimensions'][2]/2<4.05<root[2]+foot['dimensions'][2]/2
        assert root[0]<-2 and 1.1<root[1]<6.5
    assert not any(p['instance_id']=='passenger/shield-brace' for p in assembly('mage-on-chariot')['placements'])


def test_chariot_print_fixes_are_local_and_keep_equipment_mounts():
    defs=Definitions()
    for name in ('chariot','general-on-chariot','hero-on-chariot','mage-on-chariot'):
        slots={p['instance_id']:p for p in assembly(name)['placements']}
        assert slots['driver/coat']['part']=='aurelian.expansion-chariot-driver-coat@3'
        assert slots['driver/head']['part']=='aurelian.readable-head-trial@5'
        assert slots['driver/helmet']['part']=='aurelian.expansion-chariot-helmet@1'
        assert {p['part'] for n,p in slots.items() if n.endswith('/horse')}=={'aurelian.expansion-chariot-horse@3'}
    for a in index()['assemblies']:
        if 'chariot' in a['id']:continue
        assert not any('expansion-chariot-' in p['part'] for p in json.loads((ROOT/a['path']).read_text())['placements'])
    mage={p['instance_id']:p for p in assembly('mage-on-chariot')['placements']}
    robe=defs[mage['passenger/regalia']['part']].to_dict()['parameters']
    assert point(mage['passenger/regalia']['mount'],[0,.05,robe['hem_bottom_z_mm']])[2]<4.05
    current=defs['aurelian.expansion-chariot-horse@3'].to_dict()['parameters']
    old=defs['aurelian.dragon-prince-horse@7'].to_dict()['parameters']
    for side in (-1,1):
        tag=f'{side}_hind'
        assert current['leg_paths'][tag][-1]==old['leg_paths'][tag][-1]
        assert current['leg_paths'][tag][0]==old['leg_paths'][tag][0]
        a,b=current['leg_paths'][tag][1:3]
        from math import dist
        assert dist(a[0][:2],b[0][:2])+abs(a[1]-b[1])<abs(a[0][2]-b[0][2])


def test_current_chariot_ramp_covers_all_deck_edges_and_wheels_start_in_base():
    from math import sqrt
    defs=Definitions();p=defs['aurelian.expansion-chariot@5'].to_dict()['parameters']
    atoms={a['role']:a for a in p['atoms']};h=atoms['tapered_underbody'];deck=atoms['deck']
    z=deck['location'][2]-deck['dimensions'][2]/2
    bottom=h['frame_mm'][2][3]-h['depth']/2
    t=(z-bottom)/h['depth'];half=(h['radius1']+(h['radius2']-h['radius1'])*t)/sqrt(2)
    clip=atoms['underbody_width_clip']
    for axis in (0,1):
        low=max(h['frame_mm'][axis][3]-half,clip['location'][axis]-clip['dimensions'][axis]/2)
        high=min(h['frame_mm'][axis][3]+half,clip['location'][axis]+clip['dimensions'][axis]/2)
        assert low<=deck['location'][axis]-deck['dimensions'][axis]/2
        assert high>=deck['location'][axis]+deck['dimensions'][axis]/2
    for side in (-1,1):
        w=atoms[f'wheel_{side}']
        assert w['frame_mm'][2][3]-w['radius']<=-.19
    p=defs['aurelian.expansion-chariot-horse-belly-blends@2'].to_dict()['parameters']
    foot=next(a for a in p['atoms'] if a['role']=='grounded_tail_node_0')
    assert foot['location'][2]-foot['dimensions'][2]/2<0


def test_chariot_helmet_roofs_keep_outer_crowns_and_eye_centers_clear():
    defs=Definitions()
    for ref,source in [('aurelian.expansion-chariot-helmet@1','aurelian.readable-helmet-trial@5'),
                       ('aurelian.expansion-chariot-general-helmet@2','aurelian.swordmaster-sergeant-helmet-accepted-r2@5')]:
        p=defs[ref].to_dict()['parameters'];old=defs[source].to_dict()['parameters']
        a={a['role']:a for a in p['atoms']};b={a['role']:a for a in old['atoms']}
        for role in ('helmet_crown','helmet_tapered_tip','helmet_face_opening'):
            assert a[role]==b[role]
        roof=p['face_window_roof']
        assert roof['apex_z_mm']-roof['slope']*.375>.32+.42/2
        assert roof['flat_cap_width_mm']*1.3<.3
