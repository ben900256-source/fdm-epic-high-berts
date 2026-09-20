"""Publish immutable definitions for the infantry readability experiment."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.readable_infantry import build
from fdm_sculpt.components.parts import catalog

figures = [json.loads((ROOT/f'specs/experiments/upper-spear-fill-{i}-trial.json').read_text()) for i in range(1,6)]
parts, specs = build(figures, catalog())
for part in parts:
    path = ROOT/'fdm_sculpt/components/parts'/f'{part.reference}.json'
    if path.exists():
        assert json.loads(path.read_text()) == part.to_dict(), 'Use a new revision'
    else:
        path.write_text(json.dumps(part.to_dict(), indent=2)+'\n', encoding='utf-8')
for spec in specs:
    (ROOT/'specs/experiments'/f'{spec["assembly_id"]}.json').write_text(json.dumps(spec, indent=2)+'\n', encoding='utf-8')
(ROOT/'tests/fixtures/readable-infantry-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in parts}, indent=2)+'\n')
print('Published five detail parts, five fitted joins, five poses, gallery and comparison.')
