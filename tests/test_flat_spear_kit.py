import json
import pytest
from pathlib import Path

from fdm_sculpt.components.spear_kit import definitions, assembly, CLEARANCES
from fdm_sculpt.components.parts import catalog, resolve_assembly


@pytest.mark.parametrize('revision',[1,2])
def test_pinned_kit_and_interface_dimensions(revision):
    parts=definitions(revision)
    root=Path(__file__).resolve().parents[1]
    golden=json.loads((root/f'tests/fixtures/flat-spear-kit-v{revision}-golden.json').read_text())
    assert {p.reference:p.sha256 for p in parts} == golden
    saved=catalog()
    resolved=resolve_assembly(assembly(parts,revision),saved)
    assert len(resolved['placements']) == 6
    upper=[]
    for part in parts[:4]:
        p=part.to_dict()['parameters']
        atoms={a['role']:a for a in p['atoms']}
        assert atoms['shaft']['location'][2]-atoms['shaft']['dimensions'][2]/2 == 0
        if 'keyed_pin' in atoms:
            upper.append(atoms['keyed_pin']['dimensions'][::2])
            if revision == 2:
                assert atoms['insertion_stop']['dimensions'][0] > 0.8+max(CLEARANCES)+0.2
    assert upper == [[0.8,0.8],[0.8,0.8]]
    sockets=parts[-1].to_dict()['parameters']['trial']['sockets']
    assert len(sockets)==9
    assert all(s['top_z_mm']-s['floor_z_mm'] > 2 for s in sockets)
    assert [s['total_clearance_mm'] for s in sockets[-3:]] == list(CLEARANCES)
    assert parts[-1].to_dict()['parameters']['trial']['minimum_socket_wall_mm'] >= 0.75
