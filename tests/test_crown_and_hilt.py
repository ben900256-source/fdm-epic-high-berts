"""Reproducible taller plumes retain their roots; hilt mounts stay fixed."""
import json
from pathlib import Path
import pytest
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.crown_and_hilt import revised_parts

ROOT=Path(__file__).resolve().parents[1]


def test_crown_and_hilt_pins_and_preserved_fits():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/crown-and-hilt-sources.json').read_text())
    golden=json.loads((ROOT/'tests/fixtures'/manifest['golden']).read_text())
    parts=revised_parts(definitions,manifest,1001)
    assert {p.reference:p.sha256 for p in parts}==golden
    assert {ref:definitions[ref].sha256 for ref in golden}==golden
    for part in parts:
        p=part.to_dict()['parameters'];fit=p.get('plume_height_fit',p.get('crown_height_fit',p.get('hilt_fit')))
        old=definitions[fit['source']].to_dict()['parameters']
        if 'plume_height_fit' in p:
            for before,after in zip(old['atoms'],p['atoms']):
                if '_wing_feather_' not in before['role']:assert before==after
                elif before['primitive']=='sphere':
                    assert after['dimensions'][:2]==before['dimensions'][:2]
                    assert after['dimensions'][2]==pytest.approx(before['dimensions'][2]*1.35)
                    for i in range(3):
                        assert after['location'][i]-after['frame_mm'][i][2]*after['dimensions'][2]/2==pytest.approx(before['location'][i]-before['frame_mm'][i][2]*before['dimensions'][2]/2)
        elif 'crown_height_fit' in p:
            for before,after in zip(old['atoms'],p['atoms']):
                if before['role']!='helmet_tapered_tip':assert before==after
                else:
                    assert after['location'][2]-after['depth']/2==pytest.approx(before['location'][2]-before['depth']/2)
                    assert after['location'][2]+after['depth']/2==pytest.approx(before['location'][2]+before['depth']/2+.6)
                    assert 2*(after['radius2']-after['bevel'])>=.5
        else:
            for key in ('grip','mount'):assert old['landmarks'][key]==p['landmarks'][key]
            for a,b in zip(old['atoms'],p['atoms']):
                if a['role'] not in ('blade_grip','blade_pommel'):
                    assert b['location'][:2]==a['location'][:2]
                    assert b['location'][2]==pytest.approx(a['location'][2]+.55)
            assert p['landmarks']['tip'][2]==pytest.approx(old['landmarks']['tip'][2]+.55)
            assert p['landmarks']['pommel'][2]==pytest.approx(-.25)
            assert p['hilt_fit']['side_growth_per_height']<.415
            assert p['hilt_fit']['root_z_mm']>p['landmarks']['pommel'][2]-.225
            assert not any(a['role']=='guard_rising_underside' for a in p['atoms'])
            assert p['hilt_fit']['root_z_mm']>=.7
