import json
import math
import os
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.helmet_nape import revised_parts, segmented_parts_v6, ellipse_parameters, profile, ROOT_Z, JOIN_Z, ROOT_RADIUS

ROOT = Path(__file__).resolve().parents[1]


def test_nape_revisions_resolve_and_preserve_upper_helmet():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/helmet-nape-v7-golden.json').read_text())
    previous = json.loads((ROOT/'tests/fixtures/helmet-nape-golden.json').read_text())
    assert {p.reference:p.sha256 for p in segmented_parts_v6(definitions, 1001)} == previous
    for _ in range(2):
        assert {p.reference:p.sha256 for p in revised_parts(definitions, 1001)} == golden
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    old = definitions['aurelian.helmet@5'].to_dict()['parameters']
    new = definitions['aurelian.helmet@7'].to_dict()['parameters']
    for index in (0, 1, 3):
        assert old['atoms'][index] == new['atoms'][index]
    assert all(op['solver'] == 'EXACT' for op in new['operations'])
    assert definitions['aurelian.torso@4'].to_dict()['parameters']['atoms'] == definitions['aurelian.torso@2'].to_dict()['parameters']['atoms']


def test_nape_profile_is_tangent_and_stays_inside_crown():
    expected = .82*math.sqrt(1-(JOIN_Z/2.2)**2)
    derivative = -.82*JOIN_Z/(2.2**2*math.sqrt(1-(JOIN_Z/2.2)**2))
    rx, rz, center = ellipse_parameters()
    def radius(z):
        return rx*math.sqrt(1-((z-center)/rz)**2)
    assert radius(JOIN_Z) == pytest.approx(expected)
    assert radius(ROOT_Z) == pytest.approx(ROOT_RADIUS)
    assert (radius(JOIN_Z+1e-6)-radius(JOIN_Z-1e-6))/2e-6 == pytest.approx(derivative)
    for i in range(101):
        z = ROOT_Z+(JOIN_Z-ROOT_Z)*i/100
        assert radius(z) <= .82*math.sqrt(1-(z/2.2)**2)+1e-10


@pytest.mark.integration
def test_saved_nape_provenance():
    output = os.environ.get('HELMET_NAPE_REVIEW')
    if not output:
        pytest.skip('set HELMET_NAPE_REVIEW to the assembled saved review')
    proof = json.loads((Path(output)/'saved-provenance.json').read_text())
    assert proof['passes'] and proof['checks']['visual_only'] and proof['checks']['hidden_sources']
    for ref in ('aurelian.helmet@7', 'aurelian.torso@4'):
        assert proof['checks'][ref]
    # A subtraction must not add the face-opening cutter outside the crown.
    # This catches the visual artifact seen in the discarded segmented preview.
    import array
    review = json.loads((Path(output)/'viewer-review.json').read_text())
    asset = review['assets']['aurelian.helmet@7']
    values = array.array('f')
    values.frombytes((ROOT/'out/viewer/assets'/Path(asset['url']).name).read_bytes())
    assert min(values[1::6]) >= -.921
    assert max(values[1::6]) <= 1.081
    assert min(values[2::6]) == pytest.approx(-1.4, abs=.001)
