import json
from pathlib import Path

from fdm_sculpt.components.core import ComponentDefinition
from fdm_sculpt.components.parts import validate_part, resolve_assembly
from fdm_sculpt.components.wider_shield_trial import build

ROOT = Path(__file__).resolve().parents[1]


def test_wider_shield_immutable_revision_and_unchanged_attachments():
    figures = [json.loads((ROOT/f'specs/experiments/fuller-spear-infantry-{i}-trial.json').read_text())
               for i in range(1, 6)]
    refs = {'aurelian.shield@2', 'aurelian.shield@6', 'aurelian.glue-tray-five-walled@1', 'aurelian.glue-tray-five-walled@2'} | {p['part'] for s in figures for p in s['placements']}
    definitions = {ref: validate_part(ComponentDefinition.from_dict(json.loads(
        (ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text()))) for ref in refs}
    parts, specs = build(figures, definitions)
    assert {p.reference: p.sha256 for p in parts} == json.loads(
        (ROOT/'tests/fixtures/wider-shield-golden.json').read_text())
    assert parts[0].to_dict() == definitions[parts[0].reference].to_dict()
    assert parts[1].to_dict() == definitions[parts[1].reference].to_dict()
    before_base = definitions['aurelian.glue-tray-five-walled@1'].to_dict()['parameters']['atoms']
    after_base = parts[1].to_dict()['parameters']['atoms']
    for a, b in zip(before_base[1:], after_base[1:]):
        assert a['dimensions'] == b['dimensions']
        assert a['location'][1:] == b['location'][1:]
    assert parts[0].to_dict()['parameters']['landmarks'] == definitions['aurelian.shield@2'].to_dict()['parameters']['landmarks']
    for spec in specs:
        resolve_assembly(spec, definitions)
        assert spec == json.loads((ROOT/f'specs/experiments/{spec["assembly_id"]}.json').read_text())
    for before, after in zip(figures, specs):
        for a, b in zip(before['placements'], after['placements']):
            assert a['mount'] == b['mount']
            if not a['instance_id'].endswith('/shield'):
                assert a == b
