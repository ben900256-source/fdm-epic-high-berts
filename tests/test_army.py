from copy import deepcopy
import json
import math
import os
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.atelier import prepare
from fdm_sculpt.components.elves_v2 import multiply, translation
from fdm_sculpt.components.parts import catalog

ROOT = Path(__file__).resolve().parent.parent


def indexed(assembly):
    return {p['instance_id']: p for p in assembly['placements']}


def test_standard_parts_golden_and_shared_model():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/standard-bearer-v1-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    base = indexed(load_assembly(ROOT/'specs/elf-modular-visual.json', definitions))
    unit = indexed(load_assembly(ROOT/'specs/elf-unit-center-standard.json', definitions))
    solo = indexed(load_assembly(ROOT/'specs/elf-standard-bearer.json', definitions))
    assert len(unit) == 105 and len(solo) == 21
    assert 'elf-03/spear' not in unit and 'bearer-01/spear' not in solo
    assert len([p for p in unit.values() if p['part'] == 'aurelian.spear@4']) == 4
    removed = {'spear','shield','shield-insignia','equipment-joins','shield-torso-connector','shield-lower-connector'}
    for name, p in base.items():
        if name == 'elf-03/left-arm':
            assert unit[name]['part'] == 'aurelian.horn-arm@6'
            continue
        if not (name.startswith('elf-03/') and name.split('/')[1] in removed):
            assert unit[name] == p
        else:
            assert name not in unit
    for name, p in solo.items():
        if name.startswith('bearer-01/'):
            center_name = name.replace('bearer-01/', 'elf-03/')
            assert unit[center_name] == dict(p, instance_id=center_name)
    assert unit['elf-03/standard-pole']['mount'] == base['elf-03/spear']['mount']
    pole = definitions[unit['elf-03/standard-pole']['part']].to_dict()['parameters']
    cloth = definitions[unit['elf-03/banner']['part']].to_dict()['parameters']
    assert unit['elf-03/banner']['mount'] == multiply(unit['elf-03/standard-pole']['mount'],
        translation(pole['landmarks']['banner_mount']))
    assert unit['elf-03/banner-insignia']['mount'] == multiply(unit['elf-03/banner']['mount'],
        translation(cloth['landmarks']['insignia_mount']))
    assert unit['elf-03/banner-insignia']['part'] == 'aurelian.standard-insignia@1'
    assert unit['elf-03/banner-insignia']['part'] != base['elf-03/shield-insignia']['part']


def test_wide_tapered_standard_revision_and_centered_mount():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/standard-bearer-v2-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    unit = indexed(load_assembly(ROOT/'specs/elf-unit-center-standard.json', definitions))
    pole = definitions['aurelian.standard-pole@2'].to_dict()['parameters']
    cloth = definitions['aurelian.standard-banner@2'].to_dict()['parameters']
    old = definitions['aurelian.standard-banner@1'].to_dict()['parameters']
    assert cloth['design']['width_mm'] > old['design']['width_mm']
    assert cloth['design']['lower_width_mm'] < cloth['design']['width_mm']
    assert pole['landmarks']['banner_mount'][0] == 0
    assert pole['landmarks']['crossbar_left'][0] == -pole['landmarks']['crossbar_right'][0]
    assert unit['elf-03/banner']['mount'][0][3] == unit['elf-03/standard-pole']['mount'][0][3]
    # The two clipping planes have mirrored positions and slopes; the shaft
    # and hand mount retain the reviewed grip geometry.
    atoms = {a['role']: a for a in cloth['atoms']}
    left, right = atoms['taper_cut_left'], atoms['taper_cut_right']
    assert left['location'][0] == -right['location'][0]
    assert left['location'][2] == right['location'][2]
    assert left['rotation'][1] == -right['rotation'][1]
    assert pole['atoms'][0] == definitions['aurelian.standard-pole@1'].to_dict()['parameters']['atoms'][0]


def test_pole_rooted_banner_and_horn_grip():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/standard-bearer-v3-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    unit = indexed(load_assembly(ROOT/'specs/elf-unit-center-standard.json', definitions))
    assert unit['elf-03/banner']['part'] == 'aurelian.standard-banner@10'
    assert unit['elf-03/standard-pole']['part'] == 'aurelian.standard-pole@4'
    assert unit['elf-03/horn']['part'] == 'aurelian.war-horn@7'
    horn_golden = json.loads((ROOT/'tests/fixtures/war-horn-v2-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in horn_golden} == horn_golden
    assert sum(p['part']=='aurelian.shield@2' for p in unit.values()) == 4
    cloth = definitions['aurelian.standard-banner@3'].to_dict()['parameters']
    pole = definitions['aurelian.standard-pole@3'].to_dict()['parameters']
    roles = {a['role'] for a in cloth['atoms']}
    assert 'swallowtail_cut' not in roles and 'root_front_ramp' in roles
    assert math.hypot(cloth['design']['side_growth_per_height'],
                      cloth['design']['root_front_growth_per_height']) < 1
    assert cloth['design']['cloth_thickness_mm'] >= .75
    # Both bottom corners start inside the shaft, including their depth.
    for name in ('bottom_left','bottom_right'):
        point = [a+b for a,b in zip(cloth['landmarks'][name],pole['landmarks']['banner_mount'])]
        assert math.hypot(point[0],point[1]-.46) < .51
    def world(placement, point):
        m = placement['mount']
        return [sum(m[i][j]*point[j] for j in range(3))+m[i][3] for i in range(3)]
    horn = definitions[unit['elf-03/horn']['part']].to_dict()['parameters']
    arm = definitions[unit['elf-03/left-arm']['part']].to_dict()['parameters']
    assert math.dist(world(unit['elf-03/horn'],horn['landmarks']['mouthpiece']),
                     world(unit['elf-03/left-arm'],arm['landmarks']['left_palm'])) < .2


def test_slender_horn_preserves_grip_and_broad_banner_keeps_root():
    definitions = catalog()
    for name in ('war-horn-v3-golden.json','standard-bearer-v4-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/name).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    horn = definitions['aurelian.war-horn@3'].to_dict()['parameters']
    old = definitions['aurelian.war-horn@2'].to_dict()['parameters']
    assert horn['design']['bell_outer_radius_mm'] < old['design']['bell_outer_radius_mm']
    assert horn['landmarks']['bell'][2] > old['landmarks']['bell'][2]
    assert horn['landmarks']['grip'] == old['landmarks']['grip']
    old_atoms = {a['role']:a for a in old['atoms']}
    atoms = {a['role']:a for a in horn['atoms']}
    for role in ('war_horn','horn_curve_1','horn_curve_2','mouthpiece','carrying_loop','curve_blend_2'):
        assert atoms[role] == old_atoms[role]
    banner = definitions['aurelian.standard-banner@4'].to_dict()['parameters']
    pole = definitions['aurelian.standard-pole@4'].to_dict()['parameters']
    assert banner['design']['width_mm'] > 5.2
    assert banner['design']['field_lower_width_mm']/banner['design']['width_mm'] > .9
    assert banner['design']['field_height_mm'] > 5
    assert math.hypot(banner['design']['side_growth_per_height'],banner['design']['root_front_growth_per_height']) < 1
    for name in ('bottom_left','bottom_right'):
        point = [a+b for a,b in zip(banner['landmarks'][name],pole['landmarks']['banner_mount'])]
        assert math.hypot(point[0],point[1]-.46) < .51


def test_standard_star_centering_and_continuous_lining():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/standard-bearer-v5-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    banner = definitions['aurelian.standard-banner@5'].to_dict()['parameters']
    old = definitions['aurelian.standard-banner@4'].to_dict()['parameters']
    atoms = {a['role']:a for a in banner['atoms']}
    old_atoms = {a['role']:a for a in old['atoms']}
    # Keep the reviewed outline and pole attachment while replacing the lining.
    for role in ('banner_cloth','lower_attachment','lower_cut_left','lower_cut_right',
                 'root_front_ramp','panel_cut_left','panel_cut_right','hanging_tab_left','hanging_tab_right'):
        assert atoms[role] == old_atoms[role]
    assert 'soft_fold' not in atoms
    assert banner['landmarks']['insignia_mount'] == banner['landmarks']['field_center'] == [0,-.4,2.65]
    center = banner['landmarks']['field_center']
    radius = banner['design']['lining_stroke_mm']/2
    corners = [atoms[f'lining_corner_{i}']['location'] for i in range(4)]
    assert corners[0][0] == -corners[1][0] and corners[2][0] == -corners[3][0]
    assert (corners[0][2]+corners[2][2])/2 == pytest.approx(center[2])
    for i in range(4):
        edge = atoms[f'lining_edge_{i}']
        assert edge['radius'] == radius
        assert edge['start'] == corners[i] and edge['end'] == corners[(i+1)%4]
        assert atoms[f'lining_corner_{i}']['dimensions'] == [2*radius]*3
    star = definitions['aurelian.standard-insignia@1'].to_dict()['parameters']
    assert star['landmarks']['mount'] == star['landmarks']['visual_center'] == [0,0,0]
    for first,second in (('top','bottom'),('left','right')):
        assert star['landmarks'][first] == [-v for v in star['landmarks'][second]]
    # All rays have backing overlap and stay within the attached-relief depth.
    for ray in star['atoms']:
        y = ray['frame_mm'][1][3]
        assert y+ray['depth']/2 == pytest.approx(.1)
        assert y-ray['depth']/2 == pytest.approx(-.25)


def test_full_banner_lining_keeps_cloth_and_frames_taper():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/standard-banner-v6-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    banner = definitions['aurelian.standard-banner@6'].to_dict()['parameters']
    previous = definitions['aurelian.standard-banner@5'].to_dict()['parameters']
    assert [a for a in banner['atoms'] if not a['role'].startswith('lining_')] == [
        a for a in previous['atoms'] if not a['role'].startswith('lining_')]
    assert banner['landmarks']['insignia_mount'] == previous['landmarks']['insignia_mount']
    edges = [a for a in banner['atoms'] if a['role'].startswith('lining_edge_')]
    # A closed outline reaches the lower root; only the top and tiny bottom
    # closure are horizontal, leaving the taper inside the same framed area.
    for edge,next_edge in zip(edges,edges[1:]+edges[:1]):
        assert edge['end'] == next_edge['start']
        assert edge['radius'] == previous['design']['lining_stroke_mm']/2
    horizontal = [e for e in edges if e['start'][2] == e['end'][2]]
    assert len(horizontal) == 2
    assert sorted(e['start'][2] for e in horizontal) == pytest.approx([-3.49,4.99])
    assert banner['landmarks']['lining_bottom'][1] > 0  # wraps onto the root's sloped face


def test_flat_tapestry_and_lining_share_one_front_plane():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/standard-banner-v7-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    banner = definitions['aurelian.standard-banner@7'].to_dict()['parameters']
    previous = definitions['aurelian.standard-banner@6'].to_dict()['parameters']
    atoms = {a['role']:a for a in banner['atoms']}
    old_atoms = {a['role']:a for a in previous['atoms']}
    assert 'lower_attachment' not in atoms and 'root_front_ramp' not in atoms
    cloth = atoms['banner_cloth']
    assert cloth['dimensions'][2] == banner['design']['height_mm']
    assert cloth['location'][1]-cloth['dimensions'][1]/2 == -.4
    # The silhouette cuts are retained, with all four applied to one cloth solid.
    for role in ('lower_cut_left','lower_cut_right','panel_cut_left','panel_cut_right'):
        assert atoms[role] == old_atoms[role]
        assert dict(target='banner_cloth',operand=role,operation='DIFFERENCE',solver='EXACT') in banner['operations']
    edges = [a for a in atoms.values() if a['role'].startswith('lining_edge_')]
    assert len(edges) == 6
    for edge,next_edge in zip(edges,edges[1:]+edges[:1]):
        assert edge['end'] == next_edge['start']
        assert edge['start'][1] == edge['end'][1] == -.49
    assert banner['landmarks']['insignia_mount'] == previous['landmarks']['insignia_mount']
    pole = definitions['aurelian.standard-pole@4'].to_dict()['parameters']
    contact = [a+b for a,b in zip(banner['landmarks']['root_contact'],pole['landmarks']['banner_mount'])]
    assert math.hypot(contact[0],contact[1]-.46)<.51


def test_centered_banner_and_short_root_taper():
    definitions = catalog()
    for name in ('standard-banner-v8-golden.json','standard-banner-v9-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/name).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    banner = definitions['aurelian.standard-banner@9'].to_dict()['parameters']
    assert banner['atoms'] == definitions['aurelian.standard-banner@8'].to_dict()['parameters']['atoms']
    assert all(o['target']=='banner_cloth' for o in banner['operations'])
    center = banner['landmarks']['insignia_mount']
    top,bottom = banner['landmarks']['top_left'][2],banner['landmarks']['lower_edge'][2]
    assert center == banner['landmarks']['tapestry_center']
    assert center[2] == pytest.approx((top+bottom)/2)
    assert banner['design']['root_taper_height_mm'] < 1.2
    assert math.hypot(banner['design']['side_growth_per_height'],banner['design']['root_front_growth_per_height']) < 1
    atoms = {a['role']:a for a in banner['atoms']}
    assert 'root_front_ramp' in atoms
    assert banner['operations'].index(dict(target='banner_cloth',operand='root_front_ramp',operation='DIFFERENCE',solver='EXACT')) < banner['operations'].index(dict(target='banner_cloth',operand='lining_edge_0',operation='UNION',solver='EXACT'))
    for edge in (a for a in atoms.values() if a['role'].startswith('lining_edge_')):
        assert edge['start'][1] == edge['end'][1] == -.49
        assert min(edge['start'][2],edge['end'][2])-edge['radius'] > banner['landmarks']['root_ramp_top'][2]
    pole = definitions['aurelian.standard-pole@4'].to_dict()['parameters']
    for name in ('bottom_left','bottom_right','root_contact'):
        point = [a+b for a,b in zip(banner['landmarks'][name],pole['landmarks']['banner_mount'])]
        assert math.hypot(point[0],point[1]-.46) < .51


def test_raised_star_mount_preserves_banner_geometry():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/standard-banner-v10-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    old = definitions['aurelian.standard-banner@9'].to_dict()['parameters']
    new = definitions['aurelian.standard-banner@10'].to_dict()['parameters']
    assert new['atoms'] == old['atoms'] and new['operations'] == old['operations']
    assert old['landmarks']['insignia_mount'][2] < new['landmarks']['insignia_mount'][2] < new['landmarks']['field_center'][2]


def test_horn_arm_preserves_shoulder_and_extends_to_grip():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/horn-arm-v1-golden.json').read_text())
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    old = definitions['aurelian.left-arm-c@3'].to_dict()['parameters']
    new = definitions['aurelian.horn-arm@1'].to_dict()['parameters']
    assert new['atoms'][:3] == old['atoms'][:3]
    assert new['landmarks']['left_cuff'][1] < old['landmarks']['left_cuff'][1]-.85


def test_upright_horn_has_a_rising_forearm_and_outward_bell():
    definitions = catalog()
    for revision in (2,3,4,5,6):
        golden = json.loads((ROOT/f'tests/fixtures/horn-arm-v{revision}-golden.json').read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    arm = definitions['aurelian.horn-arm@6'].to_dict()['parameters']
    old = definitions['aurelian.horn-arm@3'].to_dict()['parameters']
    before = {a['role']:a for a in old['atoms']}
    after = {a['role']:a for a in arm['atoms']}
    for role in ('left_upper_arm','left_forearm'):
        assert math.dist(after[role]['start'],after[role]['end']) < .65*math.dist(before[role]['start'],before[role]['end'])
    assert after['left_upper_arm']['start'] == before['left_upper_arm']['start']
    placements = indexed(load_assembly(ROOT/'specs/elf-standard-bearer.json', definitions))
    def point(m,p):
        return [sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3)]
    m = placements['bearer-01/left-arm']['mount']
    low,high = (point(m,arm['landmarks'][key]) for key in ('left_elbow','left_cuff'))
    assert math.hypot(high[0]-low[0], high[1]-low[1]) < high[2]-low[2]
    horn = definitions['aurelian.war-horn@6'].to_dict()['parameters']['landmarks']
    m = placements['bearer-01/horn']['mount']
    axis = [sum(m[i][j]*horn['bell_axis'][j] for j in range(3)) for i in range(3)]
    assert axis[2] > .8 and axis[1] < -.3


def test_organic_horn_retains_grip_and_uses_a_rounded_lip():
    definitions = catalog()
    for name in ('war-horn-v4-golden.json','war-horn-v5-golden.json','war-horn-v6-golden.json'):
        golden = json.loads((ROOT/'tests/fixtures'/name).read_text())
        assert {ref: definitions[ref].sha256 for ref in golden} == golden
    horn = definitions['aurelian.war-horn@6'].to_dict()['parameters']
    old = definitions['aurelian.war-horn@3'].to_dict()['parameters']
    for landmark in ('mount','grip','mouthpiece','carrying_loop'):
        assert horn['landmarks'][landmark] == old['landmarks'][landmark]
    atoms = {a['role']:a for a in horn['atoms']}
    assert 'bell_rim' not in atoms and atoms['rounded_bell_lip']['primitive']=='sphere'
    assert atoms['carrying_loop']['primitive']=='sphere'
    assert horn['landmarks']['bell'][0] < old['landmarks']['bell'][0]
    assert horn['operations'][-1] == dict(target='war_horn',operand='bell_opening',operation='DIFFERENCE',solver='EXACT')


def test_model_reposition_uses_identical_component_cache_keys(tmp_path):
    original = load_assembly(ROOT/'specs/elf-standard-bearer.json')
    moved = deepcopy(original)
    for p in moved['placements']:
        p['mount'] = multiply(translation([8, 0, 0]), p['mount'])
    first = prepare(original, seed=1001, cache=tmp_path)
    second = prepare(moved, seed=1001, cache=tmp_path)
    assert {r: a['key'] for r, a in first['assets'].items()} == {
        r: a['key'] for r, a in second['assets'].items()}


def test_recipe_rejects_cycles_missing_replacements_and_bad_pins(tmp_path):
    cyclic = tmp_path/'cyclic.json'
    cyclic.write_text(json.dumps(dict(schema_version=1, assembly_id='cycle', base_assembly='cyclic.json')))
    with pytest.raises(ValueError, match='Cyclic'):
        load_assembly(cyclic)
    layout = json.loads((ROOT/'specs/elf-unit-center-standard.json').read_text())
    layout['base_assembly'] = str(ROOT/'specs/elf-modular-visual.json')
    layout['models'][0]['model'] = str(ROOT/'specs/models/elf-standard-bearer.json')
    layout['models'][0]['instance_id'] = 'elf-99'
    cyclic.write_text(json.dumps(layout))
    with pytest.raises(ValueError, match='unknown model'):
        load_assembly(cyclic)
    layout['models'][0]['instance_id'] = 'elf-03'
    layout['models'][0]['replace'] = False
    cyclic.write_text(json.dumps(layout))
    with pytest.raises(ValueError, match='already exists'):
        load_assembly(cyclic)
    model = json.loads((ROOT/'specs/models/elf-standard-bearer.json').read_text())
    model['source']['assembly'] = str(ROOT/'specs/elf-modular-visual.json')
    model['parts'][0]['definition_sha256'] = 'stale'
    cyclic.write_text(json.dumps(model))
    with pytest.raises(ValueError, match='pinned definition changed'):
        load_model(cyclic)


@pytest.mark.integration
def test_saved_standard_bearer_provenance():
    outputs = os.environ.get('ARMY_PROOF_BUILDS')
    if not outputs:
        pytest.skip('set ARMY_PROOF_BUILDS to standalone and unit review directories, separated by semicolons')
    checked = set()
    for name in outputs.split(';'):
        output = Path(name)
        job = json.loads((output/'assembly-job.json').read_text())
        provenance = json.loads((output/'saved-provenance.json').read_text())
        review = json.loads((output/'visual-review.json').read_text())
        assert provenance['passes'] and all(provenance['checks'].values())
        assert review['placements'] == len(job['assembly']['placements'])
        assert review['digitally_validated'] is False
        assert set(job['assets']) == set(review['compiled_parts']+review['reused_parts'])
        checked.update(job['assets'])
    expected = set()
    for spec in ('elf-standard-bearer.json', 'elf-unit-center-standard.json'):
        expected.update(p['part'] for p in load_assembly(ROOT/'specs'/spec)['placements'])
    assert expected <= checked
