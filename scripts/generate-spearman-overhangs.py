"""Write immutable overhang-study revisions and repin the current spearmen."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.spearman_overhangs import revised_parts, refined_parts, sleeve_part, deposited_shield_part
from fdm_sculpt.components.terrain import write_definition
from fdm_sculpt.components.elves_v2 import translation


def generate(seed):
    definitions = catalog()
    parts = revised_parts(definitions, seed)
    replacements = {p.to_dict()['parameters']['overhang_revision']['source']: p for p in parts}
    for part in parts:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
        definitions[part.reference] = part
    golden = ROOT/'tests/fixtures/spearman-overhangs-v1-golden.json'
    payload = json.dumps({p.reference:p.sha256 for p in parts}, indent=2)+'\n'
    if golden.exists() and golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    golden.write_text(payload)
    refined = refined_parts(definitions, seed)
    for part in refined:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
        definitions[part.reference] = part
        replacements[part.to_dict()['parameters']['overhang_revision']['source']] = part
    refined_golden = ROOT/'tests/fixtures/spearman-overhangs-v2-golden.json'
    payload = json.dumps({p.reference:p.sha256 for p in refined}, indent=2)+'\n'
    if refined_golden.exists() and refined_golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    refined_golden.write_text(payload)
    sleeve = sleeve_part(definitions, seed)
    write_definition(sleeve, ROOT/'fdm_sculpt/components/parts')
    replacements['aurelian.right-tunic@2'] = sleeve
    sleeve_golden = ROOT/'tests/fixtures/spearman-overhang-sleeve-golden.json'
    payload = json.dumps({sleeve.reference:sleeve.sha256}, indent=2)+'\n'
    if sleeve_golden.exists() and sleeve_golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    sleeve_golden.write_text(payload)
    shield = deposited_shield_part(definitions, seed)
    write_definition(shield, ROOT/'fdm_sculpt/components/parts')
    replacements['aurelian.shield@4'] = shield
    shield_golden = ROOT/'tests/fixtures/spearman-overhang-shield-v5-golden.json'
    payload = json.dumps({shield.reference:shield.sha256}, indent=2)+'\n'
    if shield_golden.exists() and shield_golden.read_text() != payload:
        raise ValueError('preserve reviewed golden hashes')
    shield_golden.write_text(payload)
    path = ROOT/'specs/elf-modular-visual.json'
    assembly = json.loads(path.read_text())
    for placement in assembly['placements']:
        while placement['part'] in replacements:
            part = replacements[placement['part']]
            placement.update(part=part.reference, definition_sha256=part.sha256)
    path.write_text(json.dumps(assembly, indent=2)+'\n')
    base = [dict(p) for p in assembly['placements'] if '/' not in p['instance_id']]
    plain = definitions['aurelian.base-body-20x5-plain@1']
    next(p for p in base if p['instance_id']=='strip').update(part=plain.reference, definition_sha256=plain.sha256)
    poses = ('01-standing-guard', '02-watching-left', '03-watching-right', '04-spear-forward', '05-spear-outward')
    layout = dict(schema_version=1, assembly_id='aurelian-spearmen-overhang-study',
                  label='Spearmen - tapered underside study', placements=base,
                  models=[dict(instance_id=f'row-{i+1:02}', model=f'models/spearmen/{pose}.json',
                               mount=translation([-8+4*i, 0, 1])) for i,pose in enumerate(poses)])
    (ROOT/'specs/elf-spearmen-overhang-study.json').write_text(json.dumps(layout, indent=2)+'\n')
    print(json.dumps(dict(initial_revisions=len(parts), refined_revisions=len(refined),
                         assembly='specs/elf-spearmen-overhang-study.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True, type=int)
    generate(parser.parse_args().seed)
