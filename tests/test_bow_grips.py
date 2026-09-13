import json
from pathlib import Path

from fdm_sculpt.components.bow_grips import fitted_handle
from fdm_sculpt.components.parts import catalog

ROOT = Path(__file__).resolve().parent.parent


def test_fitted_bow_grips_resolve_and_repeat_golden_definitions():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/bow-grips-v1-golden.json').read_text())
    assert len(golden) == 3
    for reference, digest in golden.items():
        definition = definitions[reference]
        parameters = definition.to_dict()['parameters']
        parent = definitions[parameters['grip_profile']['parent_reference']]
        for _ in range(2):
            assert fitted_handle(parent, definition.version).sha256 == digest == definition.sha256
        original = parent.to_dict()['parameters']
        assert parameters['atoms'][:-2] == original['atoms']
        assert parameters['operations'][:len(original['operations'])] == original['operations']
        assert parameters['landmarks'] == original['landmarks']
        assert parameters['grip_profile']['parent_sha256'] == parent.sha256
        assert parameters['grip_profile']['radius_mm'] == .4
        assert all(op['solver'] == 'EXACT' for op in parameters['operations'])
