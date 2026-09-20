import json
from pathlib import Path

import pytest

from fdm_sculpt.components import glue_base as g
from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT=Path(__file__).resolve().parents[1]


def test_pinned_parts_and_unchanged_figure_geometry():
    definitions=catalog()
    target=json.loads((ROOT/'specs/elf-print-target.json').read_text())
    source=json.loads((ROOT/target['source_assembly']).read_text())
    parts,specs=g.assemblies(source,definitions)
    golden=json.loads((ROOT/'tests/fixtures/glue-base-golden.json').read_text())
    assert {p.reference:p.sha256 for p in parts}==golden
    for p in parts:assert definitions[p.reference].to_dict()==p.to_dict()
    for spec in specs:
        assert resolve_assembly(spec,definitions)['placements']==spec['placements']
        assert json.loads((ROOT/'specs/experiments'/f'{spec["assembly_id"]}.json').read_text())==spec
    original={p['instance_id']:p for p in source['placements']}
    for i,spec in enumerate(specs[:5],1):
        for p in spec['placements'][2:]:
            old=original[p['instance_id']]
            assert p['part']==old['part'] and p['definition_sha256']==old['definition_sha256']
            for axis in range(3):
                assert p['mount'][axis][:3]==old['mount'][axis][:3]
                assert p['mount'][axis][3]==pytest.approx(old['mount'][axis][3]-((i-3)*4 if axis==0 else 0))


def test_same_flat_footings_fit_both_trays_with_structural_stock():
    width,depth,height=[v*g.SCALE for v in g.TILE]
    assert [width,depth,height]==pytest.approx([5.2,6.5,1.3])
    compact=g.tray().to_dict()['parameters']['recipe']
    walled=g.walled_tray().to_dict()['parameters']['recipe']
    assert (compact['recess_mm'][0]-width-4*compact['pitch_mm'])/2==pytest.approx(.15)
    assert compact['pitch_mm']-width==pytest.approx(.2)
    assert (walled['recess_mm'][0]-width)/2==pytest.approx(.15)
    for recipe in [compact,walled]:
        assert (recipe['recess_mm'][1]-depth)/2==pytest.approx(.15)
        assert recipe['floor_mm']>=.75 and recipe['wall_mm']>=.75
        assert height-recipe['recess_mm'][2]==pytest.approx(.1)
    assert walled['pitch_mm']-walled['recess_mm'][0]==pytest.approx(.8)
    assert (walled['outside_mm'][0]-4*walled['pitch_mm']-walled['recess_mm'][0])/2==pytest.approx(.8)
