import json,math
from pathlib import Path
import pytest
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.forward_spearmen import generate_parts
from fdm_sculpt.army import load_assembly
from fdm_sculpt.workshop import plan, public_models

ROOT=Path(__file__).resolve().parents[1]


def test_pinned_forward_poses_bases_and_permanent_contacts():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/forward-spearmen-sources.json').read_text())
    parts,poses=generate_parts(definitions,manifest,1001)
    golden=json.loads((ROOT/'tests/fixtures'/manifest['golden']).read_text())
    assert {p.reference:p.sha256 for p in parts}==golden
    assert {r:definitions[r].sha256 for r in golden}==golden
    assert [p['elevation'] for p in poses]==list(range(0,46,5))
    for pose in poses:
        m=pose['spear_mount']
        assert math.degrees(math.asin(m[2][2]))==pytest.approx(pose['elevation'])
        assert -15.5<pose['tip'][1]<2.5
        recipe=definitions[pose['support']].to_dict()['parameters']['recipe']
        assert recipe['permanent'] and len(recipe['contacts'])==4
        for contact in recipe['contacts']:
            assert -2<contact['foot'][0]<2 and -15.5<contact['foot'][1]<2.5
            assert 0<contact['shaft'][2]-contact['tip'][2]<.6
    assembly=load_assembly(ROOT/'specs/elf-forward-spearmen.json',definitions)
    assert len({p['instance_id'].split('/')[0] for p in assembly['placements'] if '/' in p['instance_id']})==10


@pytest.mark.parametrize('magnets',[False,True])
def test_forward_models_available_and_row_extensions_reach_ground(magnets):
    ids=[p['id'] for p in public_models() if 'forward-spear-' in p['id']]
    assert len(ids)==10
    row=plan(dict(seed=1001,family='spearmen',slots=ids[:5],magnet_holes=magnets))
    assert row['base_mm']==[20,18,2 if magnets else 1]
    extensions=[p for p in row['assembly']['placements'] if p['instance_id'].endswith('/forward-base-extension')]
    assert len(extensions)==5
    assert all(p['mount'][2][3]==0 for p in extensions)
    assert all(p['part']==f'aurelian.forward-base-extension@{2 if magnets else 1}' for p in extensions)
