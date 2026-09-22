"""Publish the broader shield as a new immutable revision."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.wider_shield_trial import build
from fdm_sculpt.components.core import ComponentDefinition
from fdm_sculpt.components.parts import validate_part

figures = [json.loads((ROOT/f'specs/experiments/fuller-spear-infantry-{i}-trial.json').read_text())
           for i in range(1, 6)]
refs = {'aurelian.shield@2', 'aurelian.glue-tray-five-walled@1'} | {p['part'] for s in figures for p in s['placements']}
definitions = {ref: validate_part(ComponentDefinition.from_dict(json.loads(
    (ROOT/'fdm_sculpt/components/parts'/f'{ref}.json').read_text()))) for ref in refs}
parts, specs = build(figures, definitions)
for part in parts:
    path = ROOT/'fdm_sculpt/components/parts'/f'{part.reference}.json'
    if path.exists():
        assert json.loads(path.read_text()) == part.to_dict(), 'Use a new revision'
    else:
        path.write_text(json.dumps(part.to_dict(), indent=2)+'\n', encoding='utf-8')
for spec in specs:
    (ROOT/'specs/experiments'/f'{spec["assembly_id"]}.json').write_text(
        json.dumps(spec, indent=2)+'\n', encoding='utf-8')
(ROOT/'tests/fixtures/wider-shield-golden.json').write_text(
    json.dumps({p.reference: p.sha256 for p in parts}, indent=2)+'\n')
print('Published', len(parts), 'parts and', len(specs), 'assemblies.')
