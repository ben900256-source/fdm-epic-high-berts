import json
from pathlib import Path

import pytest

from fdm_sculpt.components.flat_seahorse import build
from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('raised', [False, True])
def test_flat_seahorse_revision_and_unchanged_figure_placements(raised):
    definitions = catalog()
    source = 'flat-seahorse' if raised else 'open-arm'
    fixture = 'raised-flat-seahorse' if raised else 'flat-seahorse'
    originals = [json.loads((ROOT/f'specs/experiments/{source}-infantry-{i}-trial.json').read_text())
                 for i in range(1, 6)]
    part, specs = build(originals, definitions, raised=raised)
    assert {part.reference: part.sha256} == json.loads(
        (ROOT/f'tests/fixtures/{fixture}-golden.json').read_text())
    assert definitions[part.reference].to_dict() == part.to_dict()
    for spec in specs:
        resolve_assembly(spec, definitions)
        assert spec == json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())
    for before, after in zip(originals, specs):
        for old, new in zip(before['placements'], after['placements']):
            if old['instance_id'].endswith('/shield-insignia'):
                assert old['mount'] == new['mount']
                assert new['part'] == part.reference
            else:
                assert old == new
