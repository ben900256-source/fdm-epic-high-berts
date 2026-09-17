"""Write pinned revision-one primitive definitions and a one-off kit assembly."""
import json
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.spear_kit import definitions, assembly

parser=argparse.ArgumentParser()
parser.add_argument('--revision',type=int,default=1,choices=(1,2))
revision=parser.parse_args().revision
parts=definitions(revision)
for part in parts:
    path=ROOT/'fdm_sculpt/components/parts'/f'{part.reference}.json'
    payload=json.dumps(part.to_dict(),indent=2)+'\n'
    if path.exists() and json.loads(path.read_text()) != part.to_dict():
        raise ValueError(f'Immutable revision changed: {path}')
    path.write_text(payload)
spec=ROOT/f'specs/experiments/flat-spear-kit-v{revision}.json'
spec.parent.mkdir(parents=True,exist_ok=True)
spec.write_text(json.dumps(assembly(parts,revision),indent=2)+'\n')
golden=ROOT/f'tests/fixtures/flat-spear-kit-v{revision}-golden.json'
hashes={p.reference:p.sha256 for p in parts}
if golden.exists() and json.loads(golden.read_text()) != hashes:
    raise ValueError('Reviewed hashes changed')
golden.write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps(hashes,indent=2))
