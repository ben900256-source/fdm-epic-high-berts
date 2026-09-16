import json
from pathlib import Path

from fdm_sculpt.components.low_bases import revised_parts
from fdm_sculpt.components.parts import catalog, isolated_part, resolve_assembly

ROOT = Path(__file__).resolve().parents[1]


def test_low_base_revisions_repeat_resolve_and_keep_terrain_clearances():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/low-bases-golden.json').read_text())
    for _ in range(2):
        parts = revised_parts(definitions, 1001)
        assert {p.reference: p.sha256 for p in parts.values()} == golden
    for source, part in parts.items():
        assert definitions[part.reference].sha256 == golden[part.reference]
        resolve_assembly(isolated_part(part.reference, definitions), definitions)
        p = part.to_dict()['parameters']
        if part.family == 'base-body':
            assert p['atoms'][0]['dimensions'][2] == 1
            assert p['atoms'][0]['location'][2] == .5
            assert not p['operations']
        else:
            assert p['recipe']['relief_height'] == .5
            assert p['recipe']['boots'] == definitions[source].to_dict()['parameters']['recipe']['boots']
            assert max(max(row) for row in p['atoms'][0]['grid']['heights']) <= .5
