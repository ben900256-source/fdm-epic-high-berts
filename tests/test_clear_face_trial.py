import json
from pathlib import Path

from fdm_sculpt.components.clear_face_trial import build
from fdm_sculpt.components.parts import catalog, resolve_assembly

ROOT = Path(__file__).resolve().parents[1]


def test_clear_face_keeps_helmet_outline_nose_and_other_placements():
    definitions = catalog()
    figures = [json.loads((ROOT/f'specs/experiments/raised-flat-seahorse-infantry-{i}-trial.json').read_text())
               for i in range(1, 6)]
    parts, specs = build(figures, definitions)
    assert {p.reference: p.sha256 for p in parts} == json.loads(
        (ROOT/'tests/fixtures/clear-face-golden.json').read_text())
    for part in parts:
        assert definitions[part.reference].to_dict() == part.to_dict()
    for spec in specs:
        resolve_assembly(spec, definitions)
        assert spec == json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())
    for before, after in zip(figures, specs):
        for old, new in zip(before['placements'], after['placements']):
            assert old['mount'] == new['mount']
            if old['instance_id'].split('/')[-1] not in ('head', 'helmet'):
                assert old == new
    for part, original, changed in (
        (parts[0], definitions['aurelian.readable-head-trial@2'],
         {'cranium', 'head_envelope', 'chin_contour', 'left_cheek_hollow',
          'right_cheek_hollow', 'left_eye_socket', 'right_eye_socket', 'mouth_line'}),
        (parts[1], definitions['aurelian.helmet@7'],
         {'helmet_face_opening', 'nape_front_clearance'})):
        for old, new in zip(original.to_dict()['parameters']['atoms'], part.to_dict()['parameters']['atoms']):
            if old['role'] not in changed:
                assert old == new
