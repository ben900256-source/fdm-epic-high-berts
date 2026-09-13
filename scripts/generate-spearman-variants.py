"""Write pinned visual recipes; compile with atelier separately."""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fdm_sculpt.army import load_assembly
from fdm_sculpt.components.elves_v2 import multiply, translation
from fdm_sculpt.components.parts import catalog
from fdm_sculpt.components.spearmen import variant_parts, hunting_hawk_v2
from fdm_sculpt.components.terrain import write_definition


def rotation(axis, degrees):
    t = math.radians(degrees)
    c, s = math.cos(t), math.sin(t)
    if axis == 'x': return [[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]
    if axis == 'y': return [[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
    return [[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]]


def around(center, transform):
    return multiply(translation(center), multiply(transform, translation([-v for v in center])))


def point(m, p):
    return [sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3)]


def write(path, value):
    path = ROOT/path
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2)+'\n'
    if path.exists() and path.read_text() != text:
        raise ValueError('preserve existing recipe: '+str(path))
    path.write_text(text)


def generate(seed):
    definitions = catalog()
    parts = variant_parts(seed)
    for part in parts:
        write_definition(part, ROOT/'fdm_sculpt/components/parts')
        definitions[part.reference] = part
    write(Path('tests/fixtures/spearman-variants-v1-golden.json'), {d.reference:d.sha256 for d in parts})
    hawk = hunting_hawk_v2(seed)
    write_definition(hawk, ROOT/'fdm_sculpt/components/parts')
    definitions[hawk.reference] = hawk
    write(Path('tests/fixtures/hunting-hawk-v2-golden.json'), {hawk.reference:hawk.sha256})
    source = load_assembly(ROOT/'specs/elf-modular-visual.json', definitions)

    def placement(slot, ref, mount):
        return dict(instance_id=slot, part=ref, definition_sha256=definitions[ref].sha256, mount=mount)

    variants = [
        ('standing-guard', 'Standing guard', 0, 0, 0, 0, None),
        ('watching-left', 'Watching left', 1, -14, -24, 0, None),
        ('watching-right', 'Watching right', 2, 16, 25, 0, None),
        ('spear-forward', 'Spear angled forward', 3, -8, 0, 13, None),
        ('spear-outward', 'Spear carried outward', 4, 10, -12, -11, None),
        ('rear-rank-ready', 'Rear rank ready', 2, -20, 20, 7, None),
        ('sword-low', 'Short sword at side', 0, -10, -12, 0, 'low'),
        ('sword-guard', 'Short sword guard', 1, 14, 16, 0, 'guard'),
        ('sword-raised', 'Short sword raised', 3, -14, -16, 0, 'raised'),
        ('hawk-sergeant', 'Sergeant with hunting hawk and sword', 2, 8, -22, 0, 'raised'),
    ]
    gallery = dict(schema_version=1, assembly_id='aurelian-spearman-variants',
                   label='Spearman variants (10)', placements=[], models=[])
    index = []
    for i, (name, label, stance, yaw, look, tilt, sword) in enumerate(variants):
        number = i+1
        origin = [(stance-2)*4, 0, 1]
        slots = {p['instance_id'].split('/')[1]:dict(p, mount=multiply(translation([-v for v in origin]), p['mount']))
                 for p in source['placements'] if p['instance_id'].startswith(f'elf-{stance+1:02d}/')}
        head_center = point(slots['head']['mount'], [0, 0, 0])
        head_turn = around(head_center, rotation('z', look))
        transforms = {slot:head_turn for slot in ('head', 'helmet', 'crest')}
        removes = []
        edits = []
        if tilt:
            bow_mount = slots['spear']['mount']
            # Preserve the existing hand contact on the shaft, including its lean.
            grip = point(bow_mount, [0, .46, -.65])
            transforms['spear'] = around(grip, rotation('x' if tilt > 0 else 'y', abs(tilt)))
            removes.append('equipment-joins')
        if sword:
            removes += ['spear', 'equipment-joins', 'right-arm']
            arm_ref = 'aurelian.spearman-sword-'+sword+'-arm@1'
            arm_mount = slots['torso']['mount']
            edits.append(placement('right-arm', arm_ref, arm_mount))
            grip = definitions[arm_ref].to_dict()['parameters']['landmarks']['grip']
            edits.append(placement('shortblade', 'aurelian.shortblade@1', multiply(arm_mount,
                multiply(translation(grip), rotation('y', 24 if sword=='low' else 12)))))
        if name == 'hawk-sergeant':
            removes += ['shield', 'shield-insignia', 'shield-torso-connector', 'shield-lower-connector', 'left-arm']
            arm_ref = 'aurelian.spearman-hawk-arm@1'
            arm_mount = slots['torso']['mount']
            edits.append(placement('left-arm', arm_ref, arm_mount))
            perch = definitions[arm_ref].to_dict()['parameters']['landmarks']['perch']
            edits.append(placement('hunting-hawk', hawk.reference,
                multiply(arm_mount, multiply(translation(perch), rotation('z', -18)))))
        filename = f'{number:02d}-{name}.json'
        model = dict(schema_version=1, model_id='aurelian-spearman-'+name,
            source=dict(assembly='../../elf-modular-visual.json', figure=f'elf-{stance+1:02d}', origin_mm=origin),
            remove=removes, parts=edits, transforms=transforms, transform=rotation('z', yaw))
        write(Path('specs/models/spearmen')/filename, model)
        position = [(i%5-2)*8, (i//5)*12, 0]
        gallery['placements'] += [placement(f'base-{number:02d}', 'aurelian.base-body-4x5@1', translation(position)),
            placement(f'base-{number:02d}-terrain', 'aurelian.terrain-soil-gallery@4', translation([*position[:2], 2]))]
        gallery['models'].append(dict(instance_id=f'variant-{number:02d}-{name}',
            model='models/spearmen/'+filename, mount=translation([*position[:2], 1])))
        index.append(dict(number=number, label=label, model='models/spearmen/'+filename,
                          state='hawk-sergeant' if name=='hawk-sergeant' else 'sword' if sword else 'spear'))
    write(Path('specs/elf-spearman-variants.json'), gallery)
    write(Path('specs/spearman-variants-index.json'), dict(seed=seed, variants=index))
    sergeant = dict(schema_version=1, assembly_id='aurelian-spearman-hawk-sergeant',
        label='Spearman sergeant with hunting hawk', placements=[
            placement('base', 'aurelian.base-body-4x5@1', translation([0,0,0])),
            placement('base-terrain', 'aurelian.terrain-soil-gallery@4', translation([0,0,2]))],
        models=[dict(instance_id='sergeant-01', model='models/spearmen/10-hawk-sergeant.json', mount=translation([0,0,1]))])
    write(Path('specs/elf-spearman-hawk-sergeant.json'), sergeant)
    print('Pinned 10 variants and', len(parts), 'reusable parts; seed', seed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, required=True)
    generate(parser.parse_args().seed)
