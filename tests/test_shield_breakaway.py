import json
import os
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_breakaway import support_part

ROOT = Path(__file__).resolve().parents[1]


def test_support_candidates_repeat_and_remain_separate_from_current_row():
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/shield-breakaway-golden.json').read_text())
    for _ in range(2):
        assert {p.reference:p.sha256 for p in [support_part(1001,d) for d in (.30,.40,.50)]} == golden
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    study = load_assembly(ROOT/'specs/elf-shield-breakaway-study.json', definitions)
    current = load_assembly(ROOT/'specs/elf-spearmen-overhang-study.json', definitions)
    assert not any('breakaway' in p['part'] for p in current['placements'])
    assert sum(p['part']=='aurelian.shield@2' for p in current['placements']) == 5
    slots = {p['instance_id']:p for p in study['placements']}
    for i in range(1,4):
        prefix = f'row-{i:02}'
        assert slots[prefix+'/shield']['part'] == 'aurelian.shield@2'
        assert slots[prefix+'/breakaway-support']['mount'] == slots[prefix+'/shield']['mount']
    assert slots['row-04/shield']['part']=='aurelian.shield@2'
    assert slots['row-05/shield']['part']=='aurelian.shield@5'


@pytest.mark.integration
def test_saved_support_provenance():
    output = os.environ.get('SHIELD_BREAKAWAY_REVIEW')
    if not output:
        pytest.skip('set SHIELD_BREAKAWAY_REVIEW to the saved support comparison')
    proof = json.loads((Path(output)/'saved-provenance.json').read_text())
    assert proof['passes'] and proof['checks']['visual_only'] and proof['checks']['hidden_sources']
    for size in (30,40,50):
        assert proof['checks'][f'aurelian.shield-breakaway-{size}@1']
