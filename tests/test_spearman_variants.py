import json
import os
from pathlib import Path

import pytest

from fdm_sculpt.army import load_assembly, load_model
from fdm_sculpt.atelier import prepare
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.spearmen import variant_parts, hunting_hawk_v2

ROOT = Path(__file__).resolve().parent.parent


def point(m, p):
    return [sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3)]


def test_spearman_recipes_repeat_resolve_and_preserve_shared_parts(tmp_path):
    definitions = catalog()
    golden = json.loads((ROOT/'tests/fixtures/spearman-variants-v1-golden.json').read_text())
    for _ in range(2):
        assert {d.reference:d.sha256 for d in variant_parts(1001)} == golden
    assert {ref:definitions[ref].sha256 for ref in golden} == golden
    hawk_golden = json.loads((ROOT/'tests/fixtures/hunting-hawk-v2-golden.json').read_text())
    for _ in range(2):
        hawk = hunting_hawk_v2(1001)
        assert hawk.sha256 == definitions[hawk.reference].sha256 == hawk_golden[hawk.reference]
    variants = json.loads((ROOT/'specs/spearman-variants-index.json').read_text())['variants']
    assert len(variants) == len({v['model'] for v in variants}) == 10
    assert [v['state'] for v in variants].count('spear') == 6
    assert [v['state'] for v in variants].count('sword') == 3
    for variant in variants:
        model = load_model(ROOT/'specs'/variant['model'], definitions)
        slots = {p['instance_id']:p for p in model['placements']}
        assert slots['head']['part'] == 'aurelian.head@12'
        assert slots['helmet']['part'] == ('aurelian.sergeant-helmet@2' if variant['state']=='hawk-sergeant' else 'aurelian.helmet@7')
        assert slots['crest']['part'] == 'aurelian.crest@4'
        if variant['state'] != 'spear':
            assert 'spear' not in slots and 'equipment-joins' not in slots
            grip = definitions[slots['right-arm']['part']].to_dict()['parameters']['landmarks']['grip']
            assert point(slots['right-arm']['mount'], grip) == pytest.approx(point(slots['shortblade']['mount'], [0,0,0]))
        if variant['state'] == 'hawk-sergeant':
            assert 'shield' not in slots and 'hunting-hawk' in slots
            perch = definitions[slots['left-arm']['part']].to_dict()['parameters']['landmarks']['perch']
            assert point(slots['left-arm']['mount'], perch) == pytest.approx(point(slots['hunting-hawk']['mount'], [0,0,0]))
    assembly = load_assembly(ROOT/'specs/elf-spearman-variants.json', definitions)
    original = load_assembly(ROOT/'specs/elf-modular-visual.json', definitions)
    new_job = prepare(assembly, seed=1001, cache=tmp_path, definitions=definitions)
    old_job = prepare(original, seed=1001, cache=tmp_path, definitions=definitions)
    shared = new_job['assets'].keys() & old_job['assets'].keys()
    assert len(shared) > 30
    assert all(new_job['assets'][r]['key'] == old_job['assets'][r]['key'] for r in shared)
    for instance in json.loads((ROOT/'specs/elf-spearman-variants.json').read_text())['models']:
        assert instance['mount'][2][3] == 0
    for v in variants:
        assert json.loads((ROOT/'specs'/v['model']).read_text())['source']['origin_mm'][2] == 0


@pytest.mark.integration
def test_saved_variant_and_horn_revisions():
    outputs = os.environ.get('SPEARMAN_PROOF_BUILDS')
    if not outputs:
        pytest.skip('set SPEARMAN_PROOF_BUILDS to saved reviews separated by semicolons')
    checked = set()
    for name in outputs.split(';'):
        output = Path(name)
        provenance = json.loads((output/'saved-provenance.json').read_text())
        job = json.loads((output/'assembly-job.json').read_text())
        review = json.loads((output/'visual-review.json').read_text())
        assert provenance['passes'] and all(provenance['checks'].values())
        assert not review['digitally_validated']
        assert review['placements'] == len(job['assembly']['placements'])
        checked.update(job['assets'])
    for fixture in ('spearman-variants-v1-golden.json', 'hunting-hawk-v2-golden.json', 'archer-horn-hand-v2-golden.json', 'short-sword-v2-golden.json', 'sergeant-helmet-v1-golden.json'):
        assert set(json.loads((ROOT/'tests/fixtures'/fixture).read_text())) <= checked
