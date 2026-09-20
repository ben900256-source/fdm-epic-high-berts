import json
from pathlib import Path

import pytest

from fdm_sculpt.components.parts import catalog, resolve_assembly, inverse_rigid
from fdm_sculpt.components.elves_v2 import multiply
from fdm_sculpt.components.readable_infantry import build

ROOT = Path(__file__).resolve().parents[1]


def test_readable_trial_preserves_feet_height_and_equipment_connections():
    definitions = catalog()
    figures = [json.loads((ROOT/f'specs/experiments/upper-spear-fill-{i}-trial.json').read_text()) for i in range(1,6)]
    parts, specs = build(figures, definitions)
    assert {p.reference:p.sha256 for p in parts} == json.loads((ROOT/'tests/fixtures/readable-infantry-golden.json').read_text())
    for part in parts:
        assert part.to_dict() == definitions[part.reference].to_dict()
    for spec in specs:
        resolve_assembly(spec, definitions)
        assert spec == json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())
    for before, after in zip(figures, specs[:5]):
        old = {p['instance_id']:p for p in before['placements']}
        original_slots = {p['instance_id'].split('/')[-1]:p for p in before['placements']}
        revised_slots = {p['instance_id'].split('/')[-1]:p for p in after['placements']}
        for root, attached in (('right-arm','spear'), ('left-arm','shield'), ('shield','shield-insignia'), ('head','helmet')):
            a = multiply(inverse_rigid(original_slots[root]['mount']), original_slots[attached]['mount'])
            b = multiply(inverse_rigid(revised_slots[root]['mount']), revised_slots[attached]['mount'])
            for row_a, row_b in zip(a,b):
                assert row_b == pytest.approx(row_a, abs=1e-7)
        for p in after['placements']:
            source = old[p['instance_id']]
            slot = p['instance_id'].split('/')[-1]
            # Pure yaw retains every part's vertical position and orientation.
            if slot != 'helmet-spear-fill':
                assert p['mount'][2] == pytest.approx(source['mount'][2])
            if slot in ('footing','terrain','left-leg','right-leg','helmet','spear'):
                assert p['part'] == source['part']
                assert p['definition_sha256'] == source['definition_sha256']
            if slot in ('footing','terrain','left-leg','right-leg'):
                assert p == source
    # The center-pose comparison has no pose change to obscure detail differences.
    assert [p['mount'] for p in specs[2]['placements']] == [p['mount'] for p in figures[2]['placements']]
    face = parts[2].to_dict()['parameters']
    mouth = next(a for a in face['atoms'] if a['role'] == 'mouth_line')
    assert mouth['dimensions'][2]*1.3 == pytest.approx(.312)
    mail = parts[3].to_dict()['parameters']['chainmail']
    assert mail['rows']*mail['links_per_row'] == 112
    assert mail['outer_mm'][0]*1.3 == pytest.approx(.845)
