"""Pin a glue-in variant of the accepted intact-spear row."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.glue_base import assemblies
from fdm_sculpt.components.parts import catalog

target=json.loads((ROOT/'specs/elf-print-target.json').read_text())
source=json.loads((ROOT/target['source_assembly']).read_text())
parts,specs=assemblies(source,catalog())
for part in parts:
    path=ROOT/'fdm_sculpt/components/parts'/f'{part.reference}.json'
    data=part.to_dict()
    if path.exists():assert json.loads(path.read_text())==data, 'Use a new immutable revision'
    else:path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
for spec in specs:
    (ROOT/'specs/experiments'/f'{spec["assembly_id"]}.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
(ROOT/'tests/fixtures/glue-base-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in parts},indent=2)+'\n')
kit=dict(schema_version=1,kit_id='glue-in-spearmen',seed=1001,export_scale=1.3,
         source_target='specs/elf-print-target.json',
         figure_assemblies=[f'specs/experiments/glue-figure-{i}-trial.json' for i in range(1,6)],
         base_assemblies=['specs/experiments/glue-base-empty-trial.json',
                          'specs/experiments/glue-base-walled-empty-trial.json'],
         print_center_spacing_mm=115,physical_fit_tested=False,digitally_validated=False)
(ROOT/'specs/experiments/glue-base-kit.json').write_text(json.dumps(kit,indent=2)+'\n')
print('Pinned five figure footings and a shared tray; scale exports 130% once.')
