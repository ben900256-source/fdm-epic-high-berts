"""Publish the higher flat insignia while preserving the lower-relief trial."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.flat_seahorse import build
from fdm_sculpt.components.parts import catalog

figures = [json.loads((ROOT/f'specs/experiments/flat-seahorse-infantry-{i}-trial.json').read_text())
           for i in range(1, 6)]
part, specs = build(figures, catalog(), raised=True)
path = ROOT/'fdm_sculpt/components/parts'/f'{part.reference}.json'
if path.exists():
    assert json.loads(path.read_text()) == part.to_dict(), 'Use a new revision'
else:
    path.write_text(json.dumps(part.to_dict(), indent=2)+'\n', encoding='utf-8')
for spec in specs:
    (ROOT/'specs/experiments'/f'{spec["assembly_id"]}.json').write_text(
        json.dumps(spec, indent=2)+'\n', encoding='utf-8')
(ROOT/'tests/fixtures/raised-flat-seahorse-golden.json').write_text(
    json.dumps({part.reference: part.sha256}, indent=2)+'\n')
print('Published', part.reference, 'and', len(specs), 'assemblies.')
