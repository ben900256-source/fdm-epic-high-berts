import json
from pathlib import Path
import pytest
from fdm_sculpt.components.bolder_faces import SOURCES, revised_parts
from fdm_sculpt.components.recessed_face import revised_part
from fdm_sculpt.components.raised_insignia import revised_part as raised_insignia
from fdm_sculpt.components.larger_crest import revised_part as larger_crest
from fdm_sculpt.components.fierce_insignia import revised_part as fierce_insignia
from fdm_sculpt.components.parts import resolve_assembly
from test_accepted_army import Definitions

ROOT = Path(__file__).resolve().parents[1]


def test_bolder_face_revisions_are_immutable_and_resolve():
    defs = Definitions()
    parts = revised_parts(defs)
    expected = json.loads((ROOT/'tests/fixtures/bolder-faces-golden.json').read_text())
    assert {p.reference:p.sha256 for p in parts.values()} == expected
    for old, part in parts.items():
        assert defs[part.reference].to_dict() == part.to_dict()
        assert part.to_dict()['parameters']['bolder_face']['source_sha256'] == defs[old].sha256
        assert part.to_dict()['parameters']['landmarks']['mount'] == [0,0,0]


def test_detail_growth_preserves_eye_height_and_nose_underside():
    defs = Definitions()
    old = defs[SOURCES[0]].to_dict()['parameters']
    new = defs['aurelian.readable-head-trial@4'].to_dict()['parameters']
    a = {v['role']:v for v in old['atoms']}
    b = {v['role']:v for v in new['atoms']}
    assert b['cranium']['dimensions'][0] == pytest.approx(a['cranium']['dimensions'][0]*1.08)
    assert b['cranium']['dimensions'][2] == a['cranium']['dimensions'][2]
    assert b['nose_rising_envelope'] == a['nose_rising_envelope']
    for eye in ('left_eye_socket','right_eye_socket'):
        assert b[eye]['frame_mm'][2][3] == a[eye]['frame_mm'][2][3]
        assert b[eye]['dimensions'][2] > a[eye]['dimensions'][2]
        assert b[eye]['frame_mm'][1][3]+b[eye]['dimensions'][1]/2 > a[eye]['frame_mm'][1][3]+a[eye]['dimensions'][1]/2
    assert b['nose_bridge']['dimensions'][0] > a['nose_bridge']['dimensions'][0]
    assert b['nose_bridge']['frame_mm'][1][3] < a['nose_bridge']['frame_mm'][1][3]
    assert new['operations'] == old['operations']


def test_helmet_ornaments_and_other_equipment_are_preserved():
    defs = Definitions()
    allowed = {'helmet_crown','nape_ellipsoid','dragon_crown','helmet_tapered_tip',
               'helmet_face_opening','face_opening','nape_front_clearance'}
    for ref, part in revised_parts(defs).items():
        if ref == SOURCES[0]:continue
        old = defs[ref].to_dict()['parameters']
        new = part.to_dict()['parameters']
        for a,b in zip(old['atoms'], new['atoms']):
            if a['role'] not in allowed:assert a == b
            if a['role'] in ('helmet_face_opening','face_opening'):
                assert b['dimensions'][0] > a['dimensions'][0]
                assert b['dimensions'][1] > a['dimensions'][1]
                assert b['dimensions'][2] > a['dimensions'][2]
        assert old['operations'] == new['operations']


def test_head_is_recessed_and_prior_nose_is_restored():
    defs = Definitions()
    part = revised_part(defs)
    expected = json.loads((ROOT/'tests/fixtures/recessed-face-golden.json').read_text())
    assert {part.reference: part.sha256} == expected
    old = defs['aurelian.readable-head-trial@4'].to_dict()['parameters']
    prior = defs['aurelian.readable-head-trial@3'].to_dict()['parameters']
    new = part.to_dict()['parameters']
    assert new['recessed_face']['rearward_shift_mm'] == pytest.approx(.22)
    old_cranium = next(a for a in old['atoms'] if a['role']=='cranium')
    new_cranium = next(a for a in new['atoms'] if a['role']=='cranium')
    assert new_cranium['location'][1] == pytest.approx(old_cranium['location'][1] + .22)
    prior_nose = next(a for a in prior['atoms'] if a['role']=='nose_bridge')
    new_nose = next(a for a in new['atoms'] if a['role']=='nose_bridge')
    assert new_nose['dimensions'] == prior_nose['dimensions']
    for key in ('nose_bridge','nose_lower_tip','nose_upper_attachment'):
        assert new['landmarks'][key][1] == pytest.approx(prior['landmarks'][key][1] + .22)


def test_raised_insignia_has_extended_relief_and_ramps():
    defs = Definitions()
    part = raised_insignia(defs)
    expected = json.loads((ROOT/'tests/fixtures/raised-insignia-golden.json').read_text())
    assert {part.reference: part.sha256} == expected
    atoms = part.to_dict()['parameters']['atoms']
    ramps = [a for a in atoms if a['role'].endswith('_support_ramp')]
    relief = [a for a in atoms if not a['role'].endswith('_support_ramp')]
    assert len(ramps) == len(relief) == 17
    assert all(a['depth'] == pytest.approx(.18) for a in ramps)
    assert all(a['depth'] == pytest.approx(.56) for a in relief)
    assert all(a['export'] is False for a in ramps)
    assert len(part.to_dict()['parameters']['operations']) == 33



def test_larger_crest_preserves_mount_and_grows_proudly():
    defs = Definitions(); part = larger_crest(defs)
    expected = json.loads((ROOT/'tests/fixtures/larger-crest-golden.json').read_text())
    assert {part.reference: part.sha256} == expected
    old=defs['aurelian.crest@4'].to_dict()['parameters'];new=part.to_dict()['parameters']
    assert new['landmarks']['mount'] == old['landmarks']['mount']
    old_atoms={a['role']:a for a in old['atoms']};new_atoms={a['role']:a for a in new['atoms']}
    for role in ('helmet_leaf_crest','helmet_crest_spine'):
        assert new_atoms[role]['dimensions'][0] > old_atoms[role]['dimensions'][0]
        assert new_atoms[role]['dimensions'][2] > old_atoms[role]['dimensions'][2]
        assert new_atoms[role]['location'][1] < old_atoms[role]['location'][1]
    assert new['crest_update']['front_projection_mm'] == pytest.approx(.10)


def test_taller_helmets_and_elf_two_shield_turn_are_pinned():
    import math
    from fdm_sculpt.components.taller_helmets import revised_parts as taller_helmets
    defs=Definitions(); parts=taller_helmets(defs)
    expected=json.loads((ROOT/'tests/fixtures/taller-helmets-golden.json').read_text())
    assert {ref:p.sha256 for ref,p in parts.items()} == expected
    for ref,part in parts.items():
        old={a['role']:a for a in defs[ref].to_dict()['parameters']['atoms']}
        new={a['role']:a for a in part.to_dict()['parameters']['atoms']}
        for role in ('helmet_crown','helmet_face_opening','face_opening','dragon_crown'):
            if role in old and 'dimensions' in old[role]: assert new[role]['dimensions'][2] == pytest.approx(old[role]['dimensions'][2]*1.2)
    spec=json.loads((ROOT/'specs/elf-modular-visual.json').read_text())
    shield=next(p for p in spec['placements'] if p['instance_id']=='elf-02/shield')
    insignia=next(p for p in spec['placements'] if p['instance_id']=='elf-02/shield-insignia')
    assert math.degrees(math.atan2(shield['mount'][1][0],shield['mount'][0][0])) == pytest.approx(18)
    assert insignia['mount'] == shield['mount']


def test_fierce_seahorse_sharpens_head_and_snout():
    defs=Definitions();part=fierce_insignia(defs)
    expected=json.loads((ROOT/'tests/fixtures/fierce-insignia-golden.json').read_text())
    assert {part.reference:part.sha256}==expected
    p=part.to_dict()['parameters'];atoms={a['role']:a for a in p['atoms']}
    old=defs['aurelian.readable-insignia-trial@5'].to_dict()['parameters']['atoms'];old={a['role']:a for a in old}
    assert atoms['seahorse_snout']['scale'][0] < old['seahorse_snout']['scale'][0]
    assert atoms['seahorse_snout']['scale'][1] > old['seahorse_snout']['scale'][1]
    assert 'seahorse_brow' in atoms and len(p['operations']) == 34
