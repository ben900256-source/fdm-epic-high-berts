"""Save three support candidates in a separate five-figure comparison review."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.shield_breakaway import support_part
from fdm_sculpt.components.terrain import write_definition


def generate(seed):
    definitions = catalog()
    parts = [support_part(seed, d) for d in (.30, .40, .50)]
    for part in parts:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
    golden = ROOT/'tests/fixtures/shield-breakaway-golden.json'
    payload = json.dumps({p.reference:p.sha256 for p in parts}, indent=2)+'\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    assembly = deepcopy(load_assembly(ROOT/'specs/elf-spearmen-overhang-study.json', definitions))
    assembly.update(assembly_id='aurelian-shield-breakaway-study',
                    label='Shield breakaway trials - 0.30 / 0.40 / 0.50 mm')
    shield = definitions['aurelian.shield@2']
    # Three supported candidates; original shield and permanent foot controls.
    for index, figure in enumerate(('row-01', 'row-02', 'row-03', 'row-04', 'row-05')):
        placement = next(p for p in assembly['placements'] if p['instance_id']==figure+'/shield')
        if index < 4:
            placement.update(part=shield.reference, definition_sha256=shield.sha256)
        else:
            control = definitions['aurelian.shield@5']
            placement.update(part=control.reference, definition_sha256=control.sha256)
        if index < 3:
            support = parts[index]
            assembly['placements'].append(dict(instance_id=figure+'/breakaway-support',
                                                part=support.reference, definition_sha256=support.sha256,
                                                mount=deepcopy(placement['mount'])))
    path = ROOT/'specs/elf-shield-breakaway-study.json'
    path.write_text(json.dumps(assembly, indent=2)+'\n')
    print(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True, type=int)
    generate(parser.parse_args().seed)
