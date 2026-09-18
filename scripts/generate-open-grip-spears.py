"""Generate the open-palm alternative from the frozen original arm placements."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.grip_spears import assemblies

source=json.loads((ROOT/'specs/experiments/full-spear-source-row.json').read_text())
targets=ROOT/'specs/experiments/open-grip-clearance-targets.json'
parts,specs=assemblies(source,catalog(),json.loads(targets.read_text()))
def write(path,value,immutable=False):
    if immutable and path.exists() and json.loads(path.read_text())!=value:
        raise ValueError(f'Immutable revision changed: {path}')
    path.write_text(json.dumps(value,indent=2)+'\n')
for p in parts:
    write(ROOT/'fdm_sculpt/components/parts'/f'{p.reference}.json',p.to_dict(),True)
for spec in specs:
    write(ROOT/'specs/experiments'/f'{spec["assembly_id"]}.json',spec)
write(ROOT/'tests/fixtures/open-grip-spears-tapered-v11-golden.json',{p.reference:p.sha256 for p in parts},True)
print('Pinned five open grips, a full spear and a sprue; three review assemblies.')
