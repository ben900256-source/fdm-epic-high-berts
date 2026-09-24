import json
from pathlib import Path

import pytest

from fdm_sculpt.components import glue_base as g
from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT=Path(__file__).resolve().parents[1]


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
