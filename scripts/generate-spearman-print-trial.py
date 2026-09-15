"""Pin a trial stand while preserving the original reviewed chainmail."""
import json
from copy import deepcopy
from pathlib import Path
from fdm_sculpt.components.print_trial import trial_mail_skirt, spaced_trial_mail_skirt, trial_equipment_brace
from fdm_sculpt.components.terrain import write_definition
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.garment_trims import cape_fitted_mail_trim
from fdm_sculpt.components.mail_internal_fill import mail_internal_fill, spearman_join_fill

ROOT = Path(__file__).resolve().parent.parent
SEATING_Z_MM = [.01, .01, .01, .005, .01]
parts = [trial_mail_skirt(seed=1001), spaced_trial_mail_skirt(seed=1001)]
definitions = catalog()
parts.extend(cape_fitted_mail_trim(definitions[f'aurelian.cape{suffix}@2'],seed=1001,revision=7)
             for suffix in ('','-b','-c','-d','-e'))
fill = mail_internal_fill(seed=1001)
parts.append(fill)
brace = trial_equipment_brace(definitions, seed=1001)
parts.append(brace)
join_fill = spearman_join_fill(seed=1001)
parts.append(join_fill)
for part in parts:
    write_definition(part, ROOT/'fdm_sculpt/components/parts')
assembly = json.loads((ROOT/'specs/elf-modular-visual.json').read_text())
assembly.update(assembly_id='aurelian-spearmen-print-trial', label='Spearmen — first print trial')
for placement in assembly['placements']:
    if placement['part'] == 'aurelian.equipment-joins@2':
        placement.update(part=brace.reference, definition_sha256=brace.sha256)
    if placement['part'].startswith('aurelian.mail-skirt-trim'):
        replacement = next(p for p in parts if p.component_id == placement['part'].split('@')[0])
        placement.update(part=replacement.reference, definition_sha256=replacement.sha256)
        placement['mount'][2][3] += .03
first = [p for p in assembly['placements'] if p['instance_id'].startswith('elf-01/')]
helper = deepcopy(next(p for p in first if p['instance_id']=='elf-01/skirt'))
helper.update(instance_id='elf-01/mail-internal-fill',part=fill.reference,definition_sha256=fill.sha256)
first.append(helper)
first.append(dict(instance_id='elf-01/join-internal-fill',part=join_fill.reference,
                  definition_sha256=join_fill.sha256,
                  mount=[[1,0,0,-8],[0,1,0,0],[0,0,1,0],[0,0,0,1]]))
assembly['placements'] = [p for p in assembly['placements'] if '/' not in p['instance_id']]
for index in range(5):
    for original in first:
        placement = deepcopy(original)
        placement['instance_id'] = placement['instance_id'].replace('elf-01/', f'elf-{index+1:02}/')
        placement['mount'][0][3] += 4*index
        placement['mount'][2][3] += SEATING_Z_MM[index]
        assembly['placements'].append(placement)
(ROOT/'specs/elf-spearmen-print-trial.json').write_text(json.dumps(assembly, indent=2)+'\n')
(ROOT/'tests/fixtures/spearman-print-trial-golden.json').write_text(json.dumps({p.reference:p.sha256 for p in parts}, indent=2)+'\n')
print(part.reference, part.sha256)
