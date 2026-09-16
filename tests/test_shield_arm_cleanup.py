import json
from pathlib import Path

from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_arm_cleanup import revised_part

ROOT = Path(__file__).resolve().parents[1]


def test_cylinder_removed_and_surrounding_arm_preserved():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/shield-arm-cleanup-golden.json').read_text())
    for _ in range(2):
        part = revised_part(definitions, 1001)
        assert {part.reference:part.sha256} == golden
    assert definitions[part.reference].sha256 == part.sha256
    old = definitions['aurelian.left-arm@3'].to_dict()['parameters']
    new = part.to_dict()['parameters']
    assert new['atoms'] == [a for a in old['atoms'] if a['role'] != 'left_forearm']
    assert 'left_forearm' not in part.output_roles
    assert new['operations'] == old['operations']
    assert new['landmarks'] == {k:v for k,v in old['landmarks'].items() if k != 'left_forearm'}
    assembly = load_assembly(ROOT/'specs/elf-spearmen-overhang-study.json', definitions)
    assert next(p for p in assembly['placements'] if p['instance_id'] == 'row-01/left-arm')['part'] == part.reference
