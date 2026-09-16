"""Pinned detail revisions preserve the reviewed crown and equipment grips."""
import json
from pathlib import Path

from fdm_sculpt.components.infantry_detail_fit import revised_parts
from fdm_sculpt.components.parts import catalog

ROOT=Path(__file__).resolve().parents[1]


def test_detail_revision_pins_and_preserved_grips():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/infantry-detail-fit-sources.json').read_text())
    golden=json.loads((ROOT/'tests/fixtures'/manifest['golden']).read_text())
    parts=revised_parts(definitions,manifest,1001)
    assert {p.reference:p.sha256 for p in parts}==golden
    assert {ref:definitions[ref].sha256 for ref in golden}==golden
    previous=json.loads((ROOT/'specs/infantry-detail-fit-v1-sources.json').read_text())
    previous_pins=json.loads((ROOT/'tests/fixtures/infantry-detail-fit-golden.json').read_text())
    assert {p.reference:p.sha256 for p in revised_parts(definitions,previous,1001)}==previous_pins
    standard=definitions['aurelian.helmet@7'].to_dict()['parameters']
    winged=definitions['aurelian.sergeant-helmet@4'].to_dict()['parameters']
    assert winged['atoms'][:len(standard['atoms'])]==standard['atoms']
    assert winged['operations'][:len(standard['operations'])]==standard['operations']
    for part in parts:
        p=part.to_dict()['parameters']
        if 'fist_fit' not in p:continue
        old=definitions[p['fist_fit']['source']].to_dict()['parameters']
        assert p['landmarks']==old['landmarks']
        assert p['atoms'][:len(old['atoms'])]==old['atoms']
        assert p['operations'][:len(old['operations'])]==old['operations']
        assert p['fist_fit']['lateral_growth_per_height']<1
