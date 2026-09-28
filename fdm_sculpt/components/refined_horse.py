"""Continuous primitive horse volumes with a planted, staggered stance.

Only ellipsoids, tangent cone segments, bevels and ordered Exact CSG are used.
The rider's saddle and the assembly mount remain in their reviewed positions.
"""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .parts import validate_part
from .spearmen import sphere, cube


SEED = 1001
HORSE_REFERENCE = 'aurelian.dragon-prince-horse@7'
BARDING_REFERENCE = 'aurelian.dragon-prince-barding@10'


def _ellipsoid(role, center, dimensions):
    atom = sphere(role, center, dimensions)
    atom.update(segments=48, ring_count=32)
    return atom


def _frame(start, end):
    """Rigid frame whose Z axis follows a segment, without Blender imports."""
    delta = [b-a for a, b in zip(start, end)]
    length = math.sqrt(sum(v*v for v in delta))
    z = [v/length for v in delta]
    helper = [1, 0, 0] if abs(z[0]) < .9 else [0, 1, 0]
    projection = sum(a*b for a, b in zip(helper, z))
    x = [a-projection*b for a, b in zip(helper, z)]
    norm = math.sqrt(sum(v*v for v in x))
    x = [v/norm for v in x]
    y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]]
    center = [(a+b)/2 for a, b in zip(start, end)]
    return [[x[i], y[i], z[i], center[i]] for i in range(3)] + [[0, 0, 0, 1]]


def _chain(role, stations, width=1):
    """Spherical nodes joined by tangent frusta; no exposed cylinder end caps.

    A 0.004 mm overlap covers the polygonal approximation at tangent seams.
    Width scales the X dimension of chains in the YZ plane only.
    """
    if width != 1 and any(p[0] != 0 for p, _ in stations):
        raise ValueError('flattened chains must lie in the YZ plane')
    atoms = []
    for i, (center, radius) in enumerate(stations):
        atoms.append(_ellipsoid(f'{role}_node_{i}', center, [2*radius*width, 2*radius, 2*radius]))
        if not i:
            continue
        previous, r0 = stations[i-1]
        length = math.dist(previous, center)
        slope = (radius-r0)/length
        if abs(slope) >= 1:
            raise ValueError('adjacent chain spheres must not contain one another')
        unit = [(b-a)/length for a, b in zip(previous, center)]
        tangent = math.sqrt(1-slope*slope)
        start = [a-slope*r0*u for a, u in zip(previous, unit)]
        end = [b-slope*radius*u for b, u in zip(center, unit)]
        atoms.append(dict(role=f'{role}_taper_{i}', primitive='cone', export=False,
            location=[0, 0, 0], radius1=r0*tangent+.004, radius2=radius*tangent+.004,
            depth=math.dist(start, end), vertices=48, bevel=0,
            scale=[width, 1, 1], frame_mm=_frame(start, end)))
    return atoms


def _long_ellipsoid(role, start, end, width, depth):
    return dict(_ellipsoid(role, [0, 0, 0], [width, depth, math.dist(start, end)]),
                frame_mm=_frame(start, end))


def refined_steed(seed):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    atoms = _chain('barrel', [([0, -1.15, 4.57], 1.23),
                            ([0, .30, 4.48], 1.34), ([0, 1.85, 4.60], 1.29)], .96)
    atoms[0]['role'] = 'barrel'
    atoms += _chain('neck', [([0, -1.42, 4.87], 1.07), ([0, -1.98, 5.93], .92),
                           ([0, -2.32, 6.86], .76), ([0, -2.65, 7.59], .64)], .86)
    atoms += _chain('face', [([0, -2.86, 7.79], .67), ([0, -3.39, 7.57], .57),
                           ([0, -4.14, 7.23], .43), ([0, -4.48, 7.13], .44)], .90)
    # A broad cheek and a long sloping forehead replace the separate round snout.
    atoms.append(_ellipsoid('jaw', [0, -2.98, 7.31], [1.18, 1.08, 1.05]))
    landmarks = dict(mount=[0, 0, 0], ground=[0, 0, 0], saddle=[0, .3, 5.8],
                     muzzle=[0, -4.3, 7.25])
    leg_paths = {}
    for side in (-1, 1):
        fore_shift = .30*side
        hind_shift = -.28*side
        fore = [([side*.80, -1.45, 4.47], .68),
                ([side*.97, -1.65+fore_shift*.2, 3.20], .54),
                ([side*1.03, -1.95+fore_shift*.65, 2.13], .45),
                ([side*1.03, -2.13+fore_shift, .99], .43),
                ([side*1.03, -2.29+fore_shift, .53], .435)]
        hind = [([side*.78, 1.85, 4.52], .76),
                ([side*.98, 1.28+hind_shift*.25, 3.28], .61),
                ([side*1.04, 2.73+hind_shift*.6, 1.94], .46),
                ([side*1.03, 2.55+hind_shift, .99], .43),
                ([side*1.03, 2.39+hind_shift, .53], .435)]
        for kind, nodes, shift, hoof_y in [('fore', fore, fore_shift, -2.29),
                                           ('hind', hind, hind_shift, 2.39)]:
            tag = f'{side}_{kind}'
            atoms += _chain(tag, nodes)
            atoms.append(dict(role=tag+'_hoof', primitive='cone', export=False,
                location=[side*1.03, hoof_y+shift, .33], radius1=.59, radius2=.48,
                depth=.66, vertices=48, scale=[1, 1.20, 1], bevel=.055, bevel_segments=3))
            landmarks[tag+'_ground'] = [side*1.03, hoof_y+shift, 0]
            leg_paths[tag] = nodes
        # Rounded leaf ears have substantial buried roots, with shallow hollows.
        atoms.append(_long_ellipsoid(f'ear_{side}', [side*.38, -2.70, 7.95],
                                    [side*.51, -2.51, 9.13], .43, .47))
        atoms.append(_ellipsoid(f'brow_{side}', [side*.49, -3.20, 8.015], [.32, .66, .25]))
    atoms += _chain('mane', [([0, -.68, 5.48], .40), ([0, -1.05, 6.33], .42),
                           ([0, -1.64, 7.27], .39), ([0, -2.30, 8.02], .32)], .65)
    atoms += _chain('tail', [([0, 2.77, 4.77], .44), ([.13, 3.24, 4.21], .49),
                           ([.30, 3.66, 3.39], .43), ([.38, 3.78, 2.61], .31),
                           ([.30, 3.51, 2.06], .13)])
    root = 'barrel'
    atoms[0]['export'] = True
    operations = [dict(target=root, operand=a['role'], operation='UNION', solver='EXACT') for a in atoms[1:]]

    def cut(atom):
        atoms.append(atom)
        operations.append(dict(target=root, operand=atom['role'], operation='DIFFERENCE', solver='EXACT'))

    for side in (-1, 1):
        cut(_ellipsoid(f'eye_socket_{side}', [side*.585, -3.20, 7.88], [.31, .47, .30]))
        cut(_long_ellipsoid(f'ear_hollow_{side}', [side*.41, -2.91, 8.24],
                            [side*.49, -2.66, 8.92], .23, .25))
        cut(_ellipsoid(f'nostril_{side}', [side*.355, -4.56, 7.32], [.30, .40, .26]))
        # Shallow oblique divisions, through the hair surface only.
        for i, (y, z) in enumerate([(-.88, 5.93), (-1.39, 6.79), (-1.97, 7.54)]):
            cut(_long_ellipsoid(f'mane_groove_{side}_{i}',
                [side*.255, y-.23, z+.30], [side*.255, y+.17, z-.27], .20, .20))
    cut(cube('mouth_line', [0, -4.73, 7.035], [1.5, .52, .18], .045))
    for i, x in enumerate((.10, .47)):
        cut(_long_ellipsoid(f'tail_groove_{i}', [x, 3.70, 3.97],
                            [x+.05, 4.025, 2.58], .19, .22))
    # Inset eyelids overlap the socket's back wall; they are not freestanding beads.
    for side in (-1, 1):
        eye = _ellipsoid(f'eye_{side}', [side*.438, -3.205, 7.88], [.22, .26, .16])
        atoms.append(eye)
        operations.append(dict(target=root, operand=eye['role'], operation='UNION', solver='EXACT'))
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id='aurelian.dragon-prince-horse', version=6,
        name='Dragon Prince steed with tapered anatomy and staggered planted hooves',
        family='dragon-prince-horse', required_anchors=['mount'], semantic_slots=['mono'],
        output_roles=[root], parameters=dict(atoms=atoms, operations=operations,
            landmarks=landmarks, seed=seed, leg_paths=leg_paths,
            provenance='Original parameterized ellipsoids and tangent frusta; local Exact CSG; visual-only.',
            design_notes='Continuous leg and neck transitions, tapered face, recessed eyes and nostrils, leaf ears, swept mane and tail. Saddle and assembly mount preserved; four grounded hooves.',
            minimum_lower_leg_diameter_mm=.86, export_scale=1.3))))


def fitted_barding(definitions, seed):
    """Fit the scalp and face armor to the new head; retain the flank plates."""
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    data = deepcopy(definitions['aurelian.dragon-prince-barding@8'].to_dict())
    data.update(version=9, name='Dragon Prince barding fitted to the tapered horse head')
    p = data['parameters']
    for atom in p['atoms']:
        role = atom['role']
        if role == 'fitted_scalp_cap':
            atom.update(location=[0, -2.94, 7.79], dimensions=[1.31, 2.04, 1.56], segments=48, ring_count=32)
        elif role == 'scalp_metal_ridge':
            atom.update(start=[0, -3.59, 8.33], end=[0, -2.65, 8.51])
        elif role == 'chamfron':
            atom.update(dimensions=[1.08, 1.91, .48], segments=48, ring_count=32)
            atom['location'][2] -= .08
        elif role == 'armored_nose':
            atom.update(location=[0, -4.18, 7.51], dimensions=[1.01, .53, .35], bevel=.09)
    p.update(seed=seed, fitted_horse='aurelian.dragon-prince-horse@6')
    return validate_part(ComponentDefinition.from_dict(data))


def apply(assembly, definitions):
    """Pin the current horse revision without moving rider or equipment mounts."""
    replacements = {'aurelian.dragon-prince-horse@5': HORSE_REFERENCE,
                    'aurelian.dragon-prince-barding@8': BARDING_REFERENCE}
    for placement in assembly['placements']:
        reference = replacements.get(placement['part'])
        if reference:
            placement.update(part=reference, definition_sha256=definitions[reference].sha256)
    if any(p['part']==HORSE_REFERENCE for p in assembly['placements']):
        assembly['label']='Dragon Prince - refined horse anatomy (visual-only)'
    return assembly


def _smooth_stations(stations, subdivisions=3):
    """Sample a pinned Catmull-Rom centerline and radius into primitive stations."""
    result = []
    values = [list(p)+[r] for p, r in stations]
    for i in range(len(values)-1):
        p0, p1, p2, p3 = [values[min(max(j, 0), len(values)-1)] for j in (i-1, i, i+1, i+2)]
        for step in range(subdivisions):
            t = step/subdivisions
            value = [.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
                     for a, b, c, d in zip(p0, p1, p2, p3)]
            result.append((value[:3], value[3]))
    return result+[(list(stations[-1][0]), stations[-1][1])]


def refined_steed_v7(seed):
    """Polish the reviewed first pass: closed lips and continuous hair channels."""
    data = refined_steed(seed).to_dict()
    data.update(version=7, name='Dragon Prince steed with flowing anatomy and a planted staggered stance')
    p = data['parameters']
    remove = {a['role'] for a in p['atoms'] if
              a['role'].startswith(('tail_', 'mane_', 'jaw')) or a['role']=='mouth_line' or
              (a['role'].startswith(('-1_fore_', '1_fore_', '-1_hind_', '1_hind_')) and not a['role'].endswith('_hoof'))}
    p['atoms'] = [a for a in p['atoms'] if a['role'] not in remove]
    p['operations'] = [o for o in p['operations'] if o['operand'] not in remove]

    def add_group(atoms, operation='UNION'):
        p['atoms'].extend(atoms)
        if operation=='UNION':
            p['operations'].extend(dict(target='barrel', operand=a['role'], operation='UNION', solver='EXACT') for a in atoms)
        else:
            root = atoms[0]['role']
            p['operations'].extend(dict(target=root, operand=a['role'], operation='UNION', solver='EXACT') for a in atoms[1:])
            p['operations'].append(dict(target='barrel', operand=root, operation='DIFFERENCE', solver='EXACT'))

    for tag, nodes in p['leg_paths'].items():
        nodes[0][0][0] = (-1 if tag.startswith('-1') else 1)*(.64 if 'fore' in tag else .56)
        add_group(_chain(tag, nodes))
    add_group([_long_ellipsoid('jaw', [0, -2.85, 7.61], [0, -3.52, 7.06], 1.04, .91)])
    mane = _smooth_stations([([0, -.68, 5.48], .40), ([0, -1.05, 6.33], .42),
                             ([0, -1.64, 7.27], .39), ([0, -2.30, 8.02], .32)])
    tail = _smooth_stations([([0, 2.77, 4.77], .44), ([.13, 3.24, 4.21], .49),
                             ([.30, 3.66, 3.39], .43), ([.38, 3.78, 2.61], .31),
                             ([.30, 3.51, 2.06], .13)])
    add_group(_chain('mane', mane, .65))
    add_group(_chain('tail', tail))
    for side in (-1, 1):
        # A long shallow channel follows each face of the mane instead of pits.
        channel = [([side*r*.65*.99, v[1]+.05, v[2]], .09) for v, r in mane[1:-1]]
        add_group(_chain(f'mane_channel_{side}', channel), 'DIFFERENCE')
        # Two grooves follow the swept tail, leaving a substantial central body.
        channel = [([v[0]+side*.17, v[1]+math.sqrt(max(.01,r*r-.17**2))-.012, v[2]], .105)
                   for v, r in tail[2:-3]]
        add_group(_chain(f'tail_channel_{side}', channel), 'DIFFERENCE')
        add_group([_ellipsoid(f'mouth_corner_{side}', [side*.365, -4.44, 6.975], [.23, .73, .18])], 'DIFFERENCE')
    add_group([_ellipsoid('lip_seam', [0, -4.891, 7.025], [.62, .19, .14])], 'DIFFERENCE')
    for atom in p['atoms']:
        if atom['primitive']=='sphere':atom.update(segments=64, ring_count=40)
        if atom['primitive']=='cone':atom['vertices']=64
    p['design_notes'] += ' Refined pass: buried limb roots, closed lips, curved hair centerlines and continuous shallow hair channels; 64-sided rounded profiles.'
    return validate_part(ComponentDefinition.from_dict(data))


def fitted_barding_v10(definitions, seed):
    data = fitted_barding(definitions, seed).to_dict()
    data.update(version=10, name='Dragon Prince face armor fitted to the flowing steed')
    data['parameters']['fitted_horse']='aurelian.dragon-prince-horse@7'
    return validate_part(ComponentDefinition.from_dict(data))
