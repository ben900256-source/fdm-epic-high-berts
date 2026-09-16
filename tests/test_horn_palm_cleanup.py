"""Revision resolution and retained geometry for the horn palm cleanup."""
import json
from pathlib import Path

from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.horn_palm_cleanup import revised_arm

ROOT = Path(__file__).resolve().parents[1]


def test_palm_cleanup_golden_and_retained_grip():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/horn-palm-cleanup-golden.json').read_text())
    for _ in range(2):
        part = revised_arm(definitions, 1001)
        assert {part.reference: part.sha256} == golden
    assert definitions[part.reference].sha256 == part.sha256
    current = part.to_dict()['parameters']
    source = definitions['aurelian.horn-arm@10'].to_dict()['parameters']
    assert current['atoms'] == [a for a in source['atoms'] if a['role'] != 'left_palm']
    assert current['operations'] == source['operations']
    assert current['cloth_pose'] == source['cloth_pose']
    assert 'left_palm' not in part.output_roles
    for role in ('left_thumb', 'left_grouped_fingers', 'robe_sleeve'):
        assert role in part.output_roles
