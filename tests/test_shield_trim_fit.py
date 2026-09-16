"""Pinned shield recesses propagate only to figures carrying shields."""
import json
from pathlib import Path

import pytest

from fdm_sculpt.army import load_model
from fdm_sculpt.components.elves_v2 import multiply
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_trim_fit import revised_parts
from fdm_sculpt.components.shield_tuck import inverse_rigid
from fdm_sculpt.workshop import models

ROOT = Path(__file__).resolve().parents[1]


def test_pinned_trim_recesses_and_live_pose_resolution():
    definitions = catalog()
    manifest = json.loads((ROOT / 'specs/shield-trim-fit-sources.json').read_text())
    golden = json.loads((ROOT / 'tests/fixtures/shield-trim-fit-v11-golden.json').read_text())
    assert {p.reference: p.sha256 for p in revised_parts(definitions, manifest, 1001)} == golden
    assert {ref: definitions[ref].sha256 for ref in golden} == golden
    for version in (9, 10):
        historical=json.loads((ROOT / f'specs/shield-trim-fit-v{version}-sources.json').read_text())
        pins=json.loads((ROOT / f'tests/fixtures/shield-trim-fit-v{version}-golden.json').read_text())
        assert {p.reference:p.sha256 for p in revised_parts(definitions,historical,1001)}==pins
    for model in models():
        placements = {p['instance_id']: p for p in load_model(model['path'], definitions)['placements']}
        if 'skirt-trim' not in placements:
            continue
        trim = definitions[placements['skirt-trim']['part']]
        if 'shield' not in placements:
            assert 'shield_trim_fit' not in trim.to_dict()['parameters']
            continue
        fit = trim.to_dict()['parameters']['shield_trim_fit']
        relative = multiply(inverse_rigid(placements['skirt-trim']['mount']), placements['shield']['mount'])
        for a, b in zip(relative, fit['shield_in_trim_frame']):
            assert a == pytest.approx(b, abs=1e-8)
