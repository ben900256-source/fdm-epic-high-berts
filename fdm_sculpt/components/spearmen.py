"""Original reusable sword arms and perched hunting hawk; no Blender imports."""
from .core import ComponentDefinition
from .parts import validate_part


SWORD_POSES = {
    'low': ((1.3, .1, -.8), (1.65, -.55, -.6)),
    'guard': ((1.45, .05, -.55), (1.7, -1.05, .25)),
    'raised': ((1.5, .1, .15), (1.75, -.75, 1.2)),
}


def sphere(role, location, dimensions):
    return dict(role=role, primitive='sphere', export=False, location=list(location),
                dimensions=list(dimensions), segments=32, ring_count=24)


def cube(role, location, dimensions, bevel=.08):
    return dict(role=role, primitive='cube', export=False, location=list(location),
                dimensions=list(dimensions), bevel=bevel)


def link(role, start, end, radius):
    return dict(role=role, primitive='between', export=False, start=list(start),
                end=list(end), radius=radius, bevel=.035)


def part(name, atoms, landmarks, seed):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    atoms[0]['export'] = True
    root = atoms[0]['role']
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id='aurelian.'+name, version=1, name=name.replace('-', ' ').capitalize(),
        family=name, required_anchors=['mount'], semantic_slots=['mono'], output_roles=[root],
        parameters=dict(atoms=atoms, operations=[dict(target=root, operand=a['role'],
            operation='UNION', solver='EXACT') for a in atoms[1:]],
            landmarks=dict(mount=[0, 0, 0], **landmarks), seed=seed,
            provenance='Original parameterized spearman variant recipe; visual-only.'))))


def arm(name, elbow, grip, seed, *, left=False):
    side = -1 if left else 1
    shoulder = [side*.98, 0, .72]
    atoms = [sphere('shoulder', shoulder, [1.15, 1.1, 1.15]),
             link('upper_arm', shoulder, elbow, .48), sphere('elbow', elbow, [1, 1, 1]),
             link('forearm', elbow, grip, .45),
             cube('palm', grip, [1.22, 1.06, 1.05], .14),
             cube('fingers', [grip[0], grip[1]-.42, grip[2]], [1.05, .38, .8], .1),
             sphere('thumb', [grip[0]-side*.43, grip[1]-.23, grip[2]+.37], [.48, .55, .55])]
    if left:
        # The glove provides a broad continuous perch under both feet.
        atoms.append(cube('falconry_glove', [grip[0], grip[1], grip[2]+.42], [1.48, 1.22, .45], .1))
    landmarks = dict(shoulder=shoulder, elbow=list(elbow), grip=list(grip))
    if left:
        landmarks['perch'] = [grip[0], grip[1], grip[2]+.62]
    return part(name, atoms, landmarks, seed)


def hunting_hawk(seed):
    atoms = [sphere('body', [0, .08, 1.32], [1.32, 1.46, 1.85]),
             sphere('breast', [0, -.38, 1.30], [1.05, .9, 1.35]),
             sphere('neck', [0, -.12, 2.05], [.85, .9, .95]),
             sphere('head', [0, -.3, 2.40], [1.02, 1.08, .98]),
             sphere('beak_root', [0, -.82, 2.34], [.56, .63, .42]),
             sphere('hooked_beak', [0, -1.01, 2.18], [.38, .4, .48])]
    for side in (-1, 1):
        tag = 'left' if side < 0 else 'right'
        atoms.extend([link(tag+'_leg', [side*.34, 0, .08], [side*.34, .06, .68], .20),
                      sphere(tag+'_foot', [side*.34, -.14, .10], [.53, .73, .25]),
                      sphere(tag+'_folded_wing', [side*.54, .35, 1.28], [.60, 1.40, 1.68]),
                      sphere(tag+'_eye', [side*.46, -.61, 2.48], [.25, .28, .25]),
                      link(tag+'_brow', [side*.38, -.83, 2.62], [side*.52, -.37, 2.63], .14)])
        for index in range(3):
            atoms.append(sphere(f'{tag}_flight_feather_{index}',
                [side*(.65-index*.045), .48+index*.22, .95-index*.11], [.28, .66, 1.05]))
            atoms.append(link(f'{tag}_toe_{index}', [side*.34+(index-1)*.14, -.05, .10],
                [side*.34+(index-1)*.17, -.46, .07], .09))
    for index in range(3):
        atom = sphere(f'tail_feather_{index}', [(index-1)*.26, .97, .72], [.4, 1.4, .45])
        atoms.append(atom)
    return part('hunting-hawk', atoms, dict(perch=[0, 0, 0], head=[0, -.3, 2.4]), seed)


def hunting_hawk_v2(seed):
    data = hunting_hawk(seed).to_dict()
    data['version'] = 2
    data['name'] = 'Hunting hawk with swept brow and hooked beak'
    p = data['parameters']
    for a in p['atoms']:
        role = a['role']
        if role == 'head':
            a['dimensions'] = [.95, .98, .8]
        elif role == 'beak_root':
            a.clear()
            a.update(role=role, primitive='cone', export=False, location=[0,-.92,2.30],
                     radius1=.23, radius2=.09, depth=.50, vertices=4, bevel=.025,
                     rotation=[1.5707963267948966,0,0], scale=[.8,1,1])
        elif role == 'hooked_beak':
            a.clear()
            a.update(link(role, [0,-1.08,2.30], [0,-1.14,2.10], .105))
        elif role.endswith('_eye'):
            side = -1 if role.startswith('left') else 1
            a.update(location=[side*.43,-.44,2.45], dimensions=[.16,.22,.15])
        elif role.endswith('_brow'):
            side = -1 if role.startswith('left') else 1
            a.update(start=[side*.33,-.66,2.58], end=[side*.44,-.20,2.52], radius=.105)
    return validate_part(ComponentDefinition.from_dict(data))


def variant_parts(seed):
    return [arm('spearman-sword-'+name+'-arm', elbow, grip, seed)
            for name, (elbow, grip) in SWORD_POSES.items()] + [
        arm('spearman-hawk-arm', [-1.5, -.1, -.05], [-2.3, -1.05, .85], seed, left=True),
        hunting_hawk(seed)]
