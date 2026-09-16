import array
import json
import os
from pathlib import Path
import pytest

from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.cape_hems import revised_parts, HEM_RAISE
from fdm_sculpt.army import load_assembly

ROOT = Path(__file__).resolve().parents[1]


def test_hem_revisions_keep_shoulders_and_upper_outline():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/cape-hems-v4-golden.json').read_text())
    previous = json.loads((ROOT/'tests/fixtures/cape-hems-v3-golden.json').read_text())
    assert {p.reference:p.sha256 for p in revised_parts(definitions, 1001, revision=3)} == previous
    for _ in range(2):
        parts = revised_parts(definitions, 1001)
        assert {p.reference:p.sha256 for p in parts} == golden
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    current = load_assembly(ROOT/'specs/elf-spearmen-overhang-study.json', definitions)
    assert set(golden) <= {p['part'] for p in current['placements']}
    for part in parts:
        new = part.to_dict()['parameters']
        old = definitions[new['hem_revision']['source']].to_dict()['parameters']
        assert new['atoms'][1:] == old['atoms'][1:]
        a,b = old['atoms'][0],new['atoms'][0]
        assert a['frame_mm'] == b['frame_mm']
        assert a['location'][2]+a['depth']/2 == pytest.approx(b['location'][2]+b['depth']/2)
        assert b['location'][2]-b['depth']/2 == pytest.approx(a['location'][2]-a['depth']/2+HEM_RAISE)
        assert (a['radius1']-a['radius2'])/a['depth'] == pytest.approx((b['radius1']-b['radius2'])/b['depth'])


@pytest.mark.integration
def test_saved_capes_meet_ground():
    output = os.environ.get('CAPE_HEM_REVIEW')
    if not output:
        pytest.skip('set CAPE_HEM_REVIEW to the shortened-cape row')
    output = Path(output)
    proof = json.loads((output/'saved-provenance.json').read_text())
    review = json.loads((output/'viewer-review.json').read_text())
    assert proof['passes'] and proof['checks']['visual_only'] and proof['checks']['hidden_sources']
    def heights(placement):
        asset = review['assets'][placement['part']]
        values = array.array('f')
        values.frombytes((ROOT/'out/viewer/assets'/Path(asset['url']).name).read_bytes())
        m = placement['mount']
        return [sum(m[2][j]*values[i+j] for j in range(3))+m[2][3] for i in range(0,len(values),6)]
    placements = review['assembly']['placements']
    terrain_top = max(heights(next(p for p in placements if p['instance_id']=='strip-terrain')))
    capes = [p for p in placements if p['instance_id'].endswith('/cape')]
    assert len(capes) == 5
    for cape in capes:
        assert proof['checks'][cape['part']] and proof['checks'][cape['instance_id']]
        assert min(heights(cape)) == pytest.approx(2.0, abs=.001)
        assert min(heights(cape)) < terrain_top
