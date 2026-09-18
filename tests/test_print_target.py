"""Protect the exact source and single enlargement accepted in the physical trial."""
import hashlib
import json
from pathlib import Path

import pytest

from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT = Path(__file__).resolve().parents[1]


def test_accepted_target_pins_intact_source_and_print_dimensions():
    target = json.loads((ROOT/'specs/elf-print-target.json').read_text())
    source = (ROOT/target['source_assembly']).read_bytes()
    canonical = json.dumps(json.loads(source), sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(canonical).hexdigest() == target['source_sha256']
    definitions = catalog()
    assembly = resolve_assembly(json.loads(source), definitions)
    spears = [p for p in assembly['placements'] if p['part'] == target['source_spear']]
    assert len(spears) == 5
    assert not any('open-spear-grip' in p['part'] or 'centered-grip-clearance' in p['part']
                   for p in assembly['placements'])
    shaft = next(a for a in definitions[target['source_spear']].to_dict()['parameters']['atoms']
                 if a['role'] == 'spear')
    assert shaft['radius']*2 == target['source_shaft_diameter_mm']
    scale = target['export_scale']
    assert scale == 1.3
    assert shaft['radius']*2*scale == pytest.approx(target['shaft_diameter_mm'])
    assert 8*scale == pytest.approx(target['nominal_sole_to_eye_mm'])
    assert [v*scale for v in [20,5,1]] == pytest.approx(target['base_mm'])
    evidence = json.loads((ROOT/target['evidence']).read_text())
    assert evidence['source_assembly_sha256'] == target['source_sha256']
    assert evidence['status'] == target['status'] == 'user-accepted-physical-print'
    assert evidence['digitally_validated'] is False
    assert evidence['saved_project_reopened_and_sliced'] is True
