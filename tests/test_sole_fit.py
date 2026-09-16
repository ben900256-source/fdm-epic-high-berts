"""Preserved toe, heel and clearance geometry with a smaller sole projection."""
import json
from pathlib import Path
import pytest
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.sole_fit import revised_parts

ROOT=Path(__file__).resolve().parents[1]


def test_sole_trim_preserves_boot_and_heel():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/sole-fit-sources.json').read_text())
    golden=json.loads((ROOT/'tests/fixtures/sole-fit-golden.json').read_text())
    for _ in range(2):
        parts=revised_parts(definitions,manifest,1001)
        assert {p.reference:p.sha256 for p in parts}==golden
    assert {ref:definitions[ref].sha256 for ref in golden}==golden
    for part in parts:
        p=part.to_dict()['parameters']; old=definitions[p['sole_fit']['source']].to_dict()['parameters']
        assert p['operations']==old['operations']
        toe=next(a for a in p['atoms'] if a['role'].endswith('_toe'))
        for a,b in zip(p['atoms'],old['atoms']):
            if not a['role'].endswith('_sole'):
                assert a==b
                continue
            assert a['frame_mm']==b['frame_mm']
            assert a['location'][0::2]==b['location'][0::2]
            assert a['dimensions'][0::2]==b['dimensions'][0::2]
            assert a['location'][1]+a['dimensions'][1]/2==pytest.approx(b['location'][1]+b['dimensions'][1]/2)
            assert (toe['location'][1]-toe['dimensions'][1]/2)-(a['location'][1]-a['dimensions'][1]/2)==pytest.approx(.04)
            assert a['dimensions'][1]<b['dimensions'][1]
