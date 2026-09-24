"""The default print recipe must point at the locked, current geometry."""
import hashlib
import json
from pathlib import Path
import pytest
from fdm_sculpt.components.leaning_spears import lean_degrees
from fdm_sculpt.components.parts import resolve_assembly
from test_accepted_army import Definitions
ROOT=Path(__file__).resolve().parents[1]

def test_default_target_pins_current_spearmen_and_single_export_scale():
    target=json.loads((ROOT/'specs/elf-print-target.json').read_text())
    source=json.loads((ROOT/target['source_assembly']).read_text(encoding='utf-8'))
    assert target['source_assembly']=='specs/elf-modular-visual.json'
    canonical=json.dumps(source,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical).hexdigest()==target['source_sha256']
    definitions=Definitions();assembly=resolve_assembly(source,definitions)
    spears=[p for p in assembly['placements'] if p['part']==target['source_spear']]
    assert len(spears)==5 and all(lean_degrees(p['mount'])>=6-1e-6 for p in spears)
    shaft=next(a for a in definitions[target['source_spear']].to_dict()['parameters']['atoms'] if a['role']=='spear')
    assert target['export_scale']==1.3
    assert shaft['radius']*2*target['export_scale']==pytest.approx(target['shaft_diameter_mm'])
    assert target['shaft_diameter_mm']==1.82 and target['base_mm']==[37.5,8.4,2]
    assert target['nozzle_configuration_mm']==[.4,.25,.4,.4,.4]
    recipe=json.loads((ROOT/target['print_recipe']).read_text())
    assert recipe['source_assembly']==target['source_assembly']
    assert recipe['tool']==2 and recipe['print_overrides']['complete_objects']=='0'
    assert recipe['tool_2_filament_overrides']==dict(min_print_speed='10',slowdown_below_layer_time='10')
    assert 'pending physical trial' in target['status']


def test_retired_experiments_are_removed_and_printed_provenance_is_pinned():
    assert not list((ROOT/'specs/experiments').glob('*.json'))
    baseline=json.loads((ROOT/'specs/spearmen-locked-baseline.json').read_text())
    printed=baseline['accepted_printed_shape']
    data=json.loads((ROOT/printed['assembly']).read_text())
    assert hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()==printed['canonical_json_sha256']
    assert printed['assembly'].startswith('specs/baselines/')
    current=json.loads((ROOT/baseline['current_assembly']).read_text())
    assert hashlib.sha256(json.dumps(current['placements'],sort_keys=True).encode()).hexdigest()==baseline['current_placements_sha256']
