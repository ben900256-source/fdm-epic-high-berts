import json
from pathlib import Path
import pytest
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.spear_socket_cleanup import revised_spear

ROOT=Path(__file__).resolve().parents[1]


def test_shaft_ends_inside_socket_and_preserves_blade():
    definitions=catalog()
    golden=json.loads((ROOT/'tests/fixtures/spear-socket-cleanup-golden.json').read_text())
    for _ in range(2):
        part=revised_spear(definitions,1001)
        assert {part.reference:part.sha256}==golden
    assert definitions[part.reference].sha256==part.sha256
    p=part.to_dict()['parameters']
    old=definitions['aurelian.spear@4'].to_dict()['parameters']
    assert p['atoms'][1:]==old['atoms'][1:]
    assert p['operations']==old['operations']
    assert p['atoms'][0]['start']==old['atoms'][0]['start']
    assert p['atoms'][0]['radius']==old['atoms'][0]['radius']
    band=next(a for a in p['atoms'] if a['role']=='spear_collar_band')
    shaft_top=p['landmarks']['shaft_top'][2]
    assert band['location'][2]-band['depth']/2 < shaft_top < band['location'][2]+band['depth']/2
    assert old['landmarks']['shaft_top'][2]-shaft_top==pytest.approx(.40)
