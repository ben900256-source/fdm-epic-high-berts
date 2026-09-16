import json
from pathlib import Path
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.additive_fists import revised_parts

ROOT=Path(__file__).resolve().parents[1]


def test_uncut_hands_are_preserved_and_only_additive_stock_is_added():
    definitions=catalog()
    manifest=json.loads((ROOT/'specs/additive-fists-sources.json').read_text())
    golden=json.loads((ROOT/'tests/fixtures/additive-fists-v1-golden.json').read_text())
    parts=revised_parts(definitions,manifest,1001)
    assert len(parts)==25
    assert {p.reference:p.sha256 for p in parts}==golden
    assert {r:definitions[r].sha256 for r in golden}==golden
    for part in parts:
        p=part.to_dict()['parameters']
        source=definitions[p['additive_fist_fit']['source']].to_dict()['parameters']
        original=[a for a in source['atoms'] if a['role']!='fist_rising_envelope']
        assert p['atoms'][:len(original)]==original
        assert p['landmarks']==source['landmarks']
        assert not any(op['operand']=='fist_rising_envelope' for op in p['operations'])
        additions=p['atoms'][len(original):]
        assert additions and all(a['primitive']=='cone' and a['bevel']>0 for a in additions)
        assert all(op['operation']=='UNION' for op in p['operations'][-len(additions):])
