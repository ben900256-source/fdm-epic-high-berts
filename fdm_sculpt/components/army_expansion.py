"""Original primitive recipes for the missing High Elf army roles.

Source dimensions are millimetres at the established 8 mm infantry scale.
These are independently cached visual parts, not fused manufacturing meshes.
"""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .elves_v2 import multiply, rotation, translation
from .parts import validate_part
from .refined_horse import _frame, _chain
from .spearmen import cube, sphere, link


SEED = 1001
PREFIX = 'aurelian.expansion-'


def ellipsoid(role, center, size):
    return dict(sphere(role, center, size), segments=40, ring_count=24)


def long_shape(role, start, end, width, depth):
    return dict(ellipsoid(role, [0, 0, 0], [width, depth, math.dist(start, end)]),
                frame_mm=_frame(start, end))


def taper(role, start, end, radius1, radius2, *, width=1, depth=1, vertices=40):
    return dict(role=role, primitive='cone', export=False, location=[0, 0, 0],
                radius1=radius1, radius2=radius2, depth=math.dist(start, end),
                vertices=vertices, bevel=0, scale=[width, depth, 1], frame_mm=_frame(start, end))


def cylinder(role, center, radius, depth, frame=None):
    result = dict(role=role, primitive='cylinder', export=False, location=list(center),
                  radius=radius, depth=depth, vertices=48, bevel=.045)
    if frame is not None:
        result['frame_mm'] = frame
    return result


def definition(name, atoms, seed, *, landmarks=None, cuts=(), notes='', metadata=None):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    atoms = deepcopy(atoms)
    for atom in atoms:
        atom['export'] = True
    operations = []
    for target, cutter in cuts:
        cutter = deepcopy(cutter)
        cutter['export'] = False
        atoms.append(cutter)
        operations.append(dict(target=target, operand=cutter['role'], operation='DIFFERENCE', solver='EXACT'))
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id=PREFIX+name, version=1, name=name.replace('-', ' ').capitalize(),
        family='army-expansion-'+name, required_anchors=['mount'], semantic_slots=['mono'],
        output_roles=[a['role'] for a in atoms if a['export']], parameters=dict(
            atoms=atoms, operations=operations, landmarks=dict(mount=[0, 0, 0], **(landmarks or {})),
            seed=seed, export_scale=1.3, visual_only=True,
            provenance='Original parameterized primitives, rigid frames and local ordered Exact CSG.',
            design_notes=notes, **(metadata or {})))))


def base(name, width, length, seed):
    return definition(name, [cube('base', [0, 0, .6], [width, length, 1.2], .15)], seed,
                      landmarks=dict(ground=[0, 0, 1.2]), metadata=dict(size_mm=[width, length, 1.2]))


def feather(role, root, tip, width=.85, thickness=.6):
    return long_shape(role, root, tip, width, thickness)


def giant_eagle(seed):
    # A rock, planted talons and steep swept wings provide an anchored silhouette.
    atoms = [taper('crag', [0, .4, .05], [.05, .15, 2.9], 1.55, .85, vertices=6),
             ellipsoid('body', [0, .65, 4.9], [2.9, 3.8, 4.0]),
             ellipsoid('breast', [0, -.35, 5.0], [2.7, 2.6, 3.6]),
             ellipsoid('neck', [0, -.65, 6.75], [1.75, 1.9, 2.7]),
             ellipsoid('head', [0, -1.02, 7.95], [1.85, 2.1, 1.65]),
             taper('upper_beak', [0, -1.72, 7.95], [0, -2.5, 7.64], .62, .19, width=.85),
             taper('hook', [0, -2.43, 7.78], [0, -2.54, 7.13], .28, .13)]
    for side in (-1, 1):
        atoms += [link(f'leg_{side}', [side*.65, .2, 2.15], [side*.8, .55, 3.65], .46),
                  ellipsoid(f'foot_{side}', [side*.6, -.1, 2.26], [.95, 1.8, .6]),
                  ellipsoid(f'hip_feathers_{side}', [side*.9, .7, 3.8], [1.15, 1.8, 1.85]),
                  link(f'brow_{side}', [side*.65, -1.85, 8.2], [side*.91, -1.17, 8.28], .22),
                  ellipsoid(f'eye_{side}', [side*.86, -1.6, 8.0], [.24, .4, .26])]
        for i in range(3):
            x = side*.6+(i-1)*.25
            atoms.append(link(f'talon_{side}_{i}', [x, -.08, 2.25], [x, -.93, 2.06], .16))
        atoms.append(long_shape(f'wing_shoulder_{side}', [side*1.02, .9, 4.8],
                                [side*2.3, 1.1, 7.6], 1.85, 1.05))
        for i in range(7):
            root = [side*(1.15+i*.09), .9+i*.16, 4.25+i*.22]
            tip = [side*(2.9+i*.17), 1.0+i*.30, 10.25-i*.45]
            atoms.append(feather(f'primary_{side}_{i}', root, tip, 1.02, .75))
        for i in range(4):
            atoms.append(feather(f'covert_{side}_{i}', [side*1.1, .45+i*.35, 4.5],
                                  [side*2.5, .6+i*.32, 7.35], .76, .67))
    for i in range(5):
        atoms.append(feather(f'tail_{i}', [(i-2)*.30, 1.5, 4.0],
                              [(i-2)*.40, 3.9, 2.4], .78, .63))
    return definition('giant-eagle', atoms, seed,
        landmarks=dict(ground=[0, 0, 0], saddle=[0, .5, 6.55], head=[0, -1.02, 7.95]),
        notes='Large perched eagle; hooked beak, swept brows, overlapping flight feathers and planted talons. Wings rise beside and behind the rider.')


def dragon(seed):
    atoms = _chain('trunk', [([0, -1.2, 4.25], 1.65), ([0, .7, 4.3], 2.0),
                             ([0, 2.5, 4.1], 1.55)], 1.04)
    atoms += _chain('neck', [([0, -1.6, 4.65], 1.15), ([0, -2.5, 5.9], 1.0),
                            ([0, -2.9, 7.5], .86), ([0, -3.8, 9.1], .85)])
    atoms += [ellipsoid('head', [0, -4.05, 9.3], [2.25, 2.8, 1.8]),
              ellipsoid('snout', [0, -5.35, 9.03], [1.65, 1.8, 1.03]),
              ellipsoid('jaw', [0, -4.93, 8.55], [1.72, 2.35, .7])]
    cuts = [('snout', cube('lip_recess', [0, -5.8, 8.87], [2.5, 1.4, .19], .035))]
    for side in (-1, 1):
        cuts.append(('head', ellipsoid(f'eye_socket_{side}', [side*.96, -4.65, 9.65], [.62, .75, .6])))
        cuts.append(('snout', ellipsoid(f'nostril_{side}', [side*.6, -5.85, 9.31], [.38, .43, .27])))
        atoms += [ellipsoid(f'eye_{side}', [side*.88, -4.65, 9.65], [.26, .40, .28]),
                  link(f'brow_{side}', [side*.66, -5.01, 9.99], [side*1.05, -3.93, 9.93], .26),
                  taper(f'horn_root_{side}', [side*.76, -3.45, 9.92], [side*1.12, -2.9, 10.85], .43, .31),
                  taper(f'horn_tip_{side}', [side*1.12, -2.9, 10.85], [side*1.3, -2.05, 11.35], .32, .14),
                  taper(f'cheek_fin_{side}', [side*.83, -3.7, 9.05], [side*1.8, -2.75, 9.18], .43, .15, depth=.6)]
        for kind, roots in [('fore', [[side*1.12, -1.6, 4.22], [side*1.8, -2.5, 2.55], [side*2.0, -3.08, .68]]),
                            ('hind', [[side*1.3, 2.05, 4.0], [side*2.15, 1.7, 2.2], [side*2.05, 3.25, .67]])]:
            for i in range(2):
                atoms += [taper(f'{kind}_{side}_limb_{i}', roots[i], roots[i+1], .86-i*.2, .66-i*.16),
                          ellipsoid(f'{kind}_{side}_joint_{i}', roots[i], [1.65-i*.4]*3)]
            x, y, z = roots[-1]
            atoms.append(ellipsoid(f'{kind}_{side}_foot', [x, y-.3, .48], [1.6, 2.2, .96]))
            for i in range(3):
                atoms.append(taper(f'{kind}_{side}_claw_{i}', [x+(i-1)*.44, y-.8, .4],
                                    [x+(i-1)*.46, y-1.6, .20], .24, .14))
        # Thick tapered four-sided primitives form continuous folded membranes.
        root = [side*1.35, .15, 5.4]
        wrist = [side*4.6, .4, 10.35]
        atoms += [taper(f'wing_arm_{side}', root, wrist, .64, .43),
                  ellipsoid(f'wing_knuckle_{side}', wrist, [.95, .95, .95])]
        for i in range(3):
            end = [side*(5.95-i*.35), 2.8+i*1.12, 8.7-i*1.65]
            atoms.append(taper(f'membrane_{side}_{i}', [side*1.55, 1.25+i*.30, 4.25], end,
                                1.0, .12, width=1.8, depth=.43, vertices=4))
            atoms.append(taper(f'wing_finger_{side}_{i}', wrist, end, .39, .18))
            atoms.append(link(f'membrane_root_{side}_{i}', [side*1.35, .6+i*.4, 4.6],
                               [side*2.3, 1.55+i*.4, 5.7], .55))
    atoms += _chain('tail', [([0, 3.2, 3.95], .95), ([.5, 4.75, 2.85], .74),
                            ([1.5, 5.9, 1.45], .55), ([2.6, 5.7, .63], .38),
                            ([3.3, 4.9, .44], .22)])
    for i, (y, z) in enumerate([(-2.9, 8.2), (-2.25, 6.8), (-1.3, 5.6),
                                (2.1, 5.35), (3.5, 4.55), (4.7, 3.2)]):
        atoms.append(taper(f'dorsal_spine_{i}', [0, y, z-.15], [0, y+.25, z+.9], .43, .13, width=.7, vertices=4))
    for i in range(5):
        atoms.append(ellipsoid(f'throat_plate_{i}', [0, -3.13-i*.24, 6.35+i*.48],
                               [1.32-i*.08, .42, .64]))
    return definition('dragon', atoms, seed, cuts=cuts,
        landmarks=dict(ground=[0, 0, 0], saddle=[0, .65, 6.35], head=[0, -4.05, 9.3]),
        notes='Grounded four-legged dragon with swept horns, recessed eyes, hooked snout, folded membranes, throat plates and a low curling tail. Tips retain finite caps.')


def mounted_seat(name, width, seed):
    atoms = [ellipsoid('saddle_cloth', [0, 0, -.2], [width+1.0, 2.6, .8]),
             ellipsoid('seat', [0, 0, .05], [2.3, 1.9, .65]),
             cube('pommel', [0, -.86, .25], [1.5, .4, .65], .13),
             cube('cantle', [0, .9, .25], [1.8, .42, .8], .13),
             ellipsoid('hips', [0, 0, .58], [1.9, 1.45, 1.3])]
    for side in (-1, 1):
        knee = [side*width/2, -.65, -.58]
        atoms += [link(f'thigh_{side}', [side*.52, 0, .65], knee, .56),
                  ellipsoid(f'knee_{side}', knee, [1.02, 1.12, 1.0]),
                  link(f'shin_{side}', knee, [side*width/2, -.55, -1.65], .44),
                  cube(f'boot_{side}', [side*width/2, -.78, -1.85], [.9, 1.3, .7], .18)]
    return definition(name, atoms, seed, landmarks=dict(seat=[0, 0, 0], torso=[0, 0, 2.05]),
                      notes='Saddle and straddling legs fitted to the creature; buried thigh roots and broad boots.')


def light_tack(seed):
    atoms = []
    for side in (-1, 1):
        points = [[side*.40, -4.45, 7.12], [side*.54, -3.15, 7.70],
                  [side*.64, -2.8, 7.45], [side*.66, -1.52, 5.8], [side*.83, .1, 5.9]]
        for i, (a, b) in enumerate(zip(points, points[1:])):
            atoms.append(link(f'cheek_rein_{side}_{i}', a, b, .18))
        atoms.append(ellipsoid(f'bridle_boss_{side}', [side*.53, -3.15, 7.70], [.24, .43, .43]))
    atoms.append(link('noseband', [-.42, -4.46, 7.17], [.42, -4.46, 7.17], .18))
    atoms.append(link('browband', [-.54, -3.15, 8.1], [.54, -3.15, 8.1], .16))
    return definition('light-horse-tack', atoms, seed, notes='Light bridle and low draped reins for the shared unarmored horse.')


def coat(seed):
    atoms = [ellipsoid('torso', [0, .05, 0], [2.12, 1.5, 2.2]),
             ellipsoid('collar', [0, 0, 1.12], [1.5, 1.0, .8]),
             cube('belt', [0, -.02, -.78], [2.14, 1.4, .30], .10)]
    for side in (-1, 1):
        atoms.append(long_shape(f'coat_tail_{side}', [side*.64, .4, -.6], [side*1.1, .8, -1.85], 1.0, .55))
        atoms.append(ellipsoid(f'shoulder_cloth_{side}', [side*.98, .03, .65], [1.03, 1.12, .82]))
    for i in range(3):
        atoms.append(link(f'front_fold_{i}', [(i-1)*.46, -.65, -.7], [(i-1)*.32, -.65, .6], .13))
    return definition('reaver-coat', atoms, seed, landmarks=dict(head=[0, 0, 2]),
                      notes='Short split riding coat; no armored horse plates or heavy winged pauldrons.')


def character_arms(kind, seed):
    grips = dict(general=([1.65, -1.12, 1.00], [-1.58, -1.28, .12]),
                 hero=([1.80, -.9, -.40], [-1.70, -1.2, .40]),
                 mage=([1.50, -1.20, .25], [-1.85, -1.1, .85]),
                 driver=([.88, -1.60, .15], [-.88, -1.60, .15]),
                 crew=([1.45, -1.30, .10], [-1.35, -1.15, .4]))
    right, left = grips[kind]
    atoms = []
    for side, grip in ((1, right), (-1, left)):
        shoulder = [side*.99, 0, .65]
        elbow = [side*1.5, -.28, -.35 if side==1 else -.05]
        atoms += [ellipsoid(f'shoulder_{side}', shoulder, [1.25, 1.2, 1.3]),
                  link(f'upper_arm_{side}', shoulder, elbow, .56),
                  ellipsoid(f'elbow_{side}', elbow, [1.15]*3),
                  link(f'forearm_{side}', elbow, grip, .52),
                  cube(f'palm_{side}', grip, [1.15, 1.1, 1.1], .16),
                  ellipsoid(f'thumb_{side}', [grip[0]-side*.35, grip[1]-.4, grip[2]+.23], [.5, .48, .55])]
        for i in range(3):
            atoms.append(cube(f'finger_{side}_{i}', [grip[0]+(i-1)*.3, grip[1]-.43, grip[2]-.06], [.26, .26, .7], .09))
    return definition(kind+'-arms', atoms, seed, landmarks=dict(right_grip=right, left_grip=left),
                      notes='Full sleeves and rounded grouped fingers; equipment mounts coincide with grip landmarks.')


def character_details(kind, seed):
    if kind == 'mage':
        atoms = [taper('robe', [0, .05, -4.65], [0, .05, -.8], 1.58, .99, depth=.72),
                 ellipsoid('mantle', [0, .22, .74], [2.8, 1.7, .94]),
                 ellipsoid('collar', [0, .45, 1.22], [1.65, 1.0, 1.05]),
                 cube('book', [-.95, -.87, -1.0], [.9, .72, 1.35], .1),
                 cube('book_clasp', [-.95, -1.24, -1.0], [.4, .17, .5], .04)]
        for i in range(7):
            x = (i-3)*.38
            atoms.append(long_shape(f'robe_fold_{i}', [x*.66, -.65, -.8], [x, -.95, -4.47], .27, .27))
        atoms.append(taper('mantle_gem', [0, -.62, .62], [0, -1.0, .62], .30, .20, vertices=6))
    else:
        length = 4.55 if kind=='general' else 3.6
        atoms = [long_shape('swept_cloak', [0, .65, .86], [.45, 1.45, -length], 2.5, .82),
                 cube('belt', [0, -.12, -.85], [2.3, 1.35, .3], .08)]
        for i in range(5):
            atoms.append(long_shape(f'cloak_fold_{i}', [(i-2)*.32, 1.04, .35],
                                    [(i-2)*.45+.35, 1.6, -length+.3], .25, .25))
        for side in (-1, 1):
            atoms.append(ellipsoid(f'pauldron_{side}', [side*.96, .02, .92], [1.32, 1.45, .6]))
            if kind=='general':
                for i in range(3):
                    atoms.append(feather(f'pauldron_leaf_{side}_{i}', [side*.75, .1, 1.03],
                                          [side*(1.6+i*.2), .40+i*.24, 1.2+i*.17], .48, .32))
        atoms.append(ellipsoid('breast_medallion', [0, -.79, .35], [.85, .35, .85]))
    return definition(kind+'-regalia', atoms, seed,
                      notes='Broad connected robe folds and distinct command insignia. Body-local mount; shared face and helmet remain unchanged.')


def riding_regalia(kind, seed):
    data = character_details(kind, seed).to_dict()
    data.update(component_id=PREFIX+kind+'-riding-regalia', family='army-expansion-'+kind+'-riding-regalia',
                name=kind.capitalize()+' regalia shortened for a saddle')
    for atom in data['parameters']['atoms']:
        if atom['role'].startswith(('robe', 'cloak', 'swept_cloak')) and 'frame_mm' in atom:
            atom['frame_mm'][2][3] = max(atom['frame_mm'][2][3], -.55)
            if 'dimensions' in atom:atom['dimensions'][2] *= .57
            if 'depth' in atom:atom['depth'] *= .57
    data['parameters']['design_notes']='Shortened riding cloak or robe; shared collar, book and command details.'
    return validate_part(ComponentDefinition.from_dict(data))


def staff(seed):
    atoms = [link('shaft', [0, 0, -4.5], [.5, 0, 4.1], .50),
             ellipsoid('socket', [.5, 0, 4.0], [1.3, 1.05, .95]),
             taper('crystal_lower', [.5, 0, 3.98], [.5, 0, 4.75], .25, .70, vertices=6),
             taper('crystal_upper', [.5, 0, 4.75], [.5, 0, 5.8], .70, .16, vertices=6)]
    for side in (-1, 1):
        atoms.append(taper(f'crescent_{side}', [.5+side*.4, 0, 4.0], [.5+side*1.0, 0, 4.9], .3, .16))
    return definition('mage-staff', atoms, seed, landmarks=dict(grip=[0, 0, 0], tip=[.5, 0, 5.8]),
                      notes='Substantial shaft and enclosed crystal socket; finite decorative tips.')


def sword(seed):
    atoms = [link('grip', [0, 0, -.65], [0, 0, .7], .43),
             ellipsoid('pommel', [0, 0, -.7], [.85, .7, .55]),
             cube('guard', [0, 0, .65], [1.8, .72, .42], .12),
             taper('blade', [0, 0, .75], [0, 0, 4.6], .63, .27, depth=.65, vertices=4),
             taper('tip', [0, 0, 4.6], [0, 0, 5.4], .27, .13, depth=.65, vertices=4)]
    return definition('command-sword', atoms, seed, landmarks=dict(grip=[0, 0, 0], tip=[0, 0, 5.4]))


def chariot(seed):
    atoms = [cube('deck', [0, 3.8, 2.4], [5.5, 5.4, .9], .15),
             cube('front_board', [0, 1.20, 3.35], [5.5, .78, 2.15], .18),
             link('axle', [-3.9, 3.5, 1.8], [3.9, 3.5, 1.8], .52),
             link('drawbar', [0, 2.5, 2.4], [0, -4.4, 3.6], .55),
             link('yoke', [-2.6, -3.7, 4.0], [2.6, -3.7, 4.0], .48)]
    cuts = []
    for side in (-1, 1):
        wheel_frame=multiply(translation([side*3.35, 3.5, 1.8]), rotation([0, 90, 0]))
        atoms.append(cylinder(f'wheel_{side}', [0, 0, 0], 1.8, .80, wheel_frame))
        cuts.append((f'wheel_{side}', dict(cylinder(f'rim_hollow_{side}', [0, 0, 0], 1.22, 1.1, wheel_frame), bevel=0)))
        atoms += [link(f'rail_{side}', [side*2.5, 1.2, 4.16], [side*2.5, 5.9, 3.3], .37),
                  link(f'side_board_{side}', [side*2.5, 1.35, 3.3], [side*2.5, 5.9, 2.8], .48),
                  link(f'trace_{side}', [side*2.2, 2, 2.7], [side*2.2, -4.0, 3.3], .43),
                  cylinder(f'hub_{side}', [0, 0, 0], .59, 1.13, wheel_frame)]
        for i in range(8):
            angle=math.tau*i/8
            atoms.append(link(f'spoke_{side}_{i}', [side*3.35, 3.5, 1.8],
                               [side*3.35, 3.5+1.5*math.sin(angle), 1.8+1.5*math.cos(angle)], .22))
        for i in range(3):
            atoms.append(link(f'front_fluting_{side}_{i}', [side*(.7+i*.6), .78, 2.55],
                               [side*(.7+i*.6), .78, 4.15], .13))
    return definition('chariot', atoms, seed, cuts=cuts,
        landmarks=dict(driver=[0, 2.3, 2.85], passenger=[0, 5.0, 2.85], horse_left=[-2.25, -4.4, 0], horse_right=[2.25, -4.4, 0]),
        notes='Two-wheel open-backed chariot, eight substantial spokes per wheel, raised front board, solid deck and twin trace poles.')


def bolt_thrower(seed):
    atoms = [cube('stock', [0, 0, 3.8], [1.05, 5.7, .85], .12),
             cylinder('pivot', [0, .55, 2.95], .75, 1.2),
             cube('breech', [0, 1.85, 4.1], [1.5, 1.4, 1.05], .1),
             cube('bolt_rack', [0, .3, 4.23], [2.35, 2.7, .6], .08),
             link('elevation_screw', [0, 1.7, 1.1], [0, 1.7, 3.7], .38)]
    for side in (-1, 1):
        atoms += [link(f'front_leg_{side}', [side*1.75, -1.8, .33], [side*.55, .4, 3.0], .48),
                  link(f'rear_leg_{side}', [side*1.65, 2.1, .33], [side*.5, .6, 3.0], .48),
                  cube(f'foot_front_{side}', [side*1.75, -1.8, .23], [.95, 1.2, .46], .12),
                  cube(f'foot_rear_{side}', [side*1.65, 2.1, .23], [.95, 1.2, .46], .12),
                  taper(f'bow_inner_{side}', [side*.3, -1.8, 3.93], [side*2.15, -1.98, 4.2], .58, .47, depth=.85),
                  taper(f'bow_outer_{side}', [side*2.15, -1.98, 4.2], [side*3.65, -.98, 4.56], .48, .3, depth=.85),
                  link(f'bowstring_{side}', [side*3.62, -.99, 4.56], [0, 2.06, 4.57], .30),
                  link(f'crank_{side}', [side*.65, 2.1, 4.1], [side*1.25, 2.1, 4.1], .25),
                  link(f'crank_handle_{side}', [side*1.2, 2.1, 4.1], [side*1.2, 2.7, 4.1], .28)]
    for i in range(3):
        x=(i-1)*.67
        atoms.append(link(f'loaded_bolt_{i}', [x, 1.55, 4.72], [x, -3.3, 4.72], .28))
        atoms.append(taper(f'bolt_head_{i}', [x, -3.15, 4.72], [x, -4.22, 4.72], .43, .14, depth=.75, vertices=4))
        atoms.append(cube(f'fletching_{i}', [x, 1.25, 4.72], [.65, .8, .23], .045))
    return definition('bolt-thrower', atoms, seed, landmarks=dict(ground=[0, 0, 0], loading=[0, 2.5, 4.5]),
                      notes='Broad recurved bow, three visible loaded bolts, substantial strings, crank handles and four planted legs. Prototype orientation still needs print assessment.')


def _first_pass_parts(seed=SEED):
    return [base('creature-base', 10, 14, seed), base('dragon-base', 14, 19, seed),
            base('chariot-base', 11, 22, seed), base('artillery-base', 13, 12, seed),
            giant_eagle(seed), dragon(seed), mounted_seat('eagle-seat', 3.1, seed),
            mounted_seat('dragon-seat', 4.9, seed), light_tack(seed), coat(seed),
            staff(seed), sword(seed), chariot(seed), bolt_thrower(seed)] + [
            character_arms(kind, seed) for kind in ('general', 'hero', 'mage', 'driver', 'crew')] + [
            character_details(kind, seed) for kind in ('general', 'hero', 'mage')] + [
            riding_regalia(kind, seed) for kind in ('general', 'hero', 'mage')]


# First visual review refinements. Revision 1 definitions remain immutable.
CURRENT_REVISIONS = {PREFIX+'dragon@1': PREFIX+'dragon@3',
                     PREFIX+'crew-arms@1': PREFIX+'crew-arms@2'}


def triangle_membrane(role, apex, edge_a, edge_b, thickness=.76):
    """An anisotropically scaled three-sided cylinder, not a hand-edited mesh.

    The edge is orthogonally projected to form the primitive's isosceles base.
    Bony fingers overlap the small projection differences at its corners.
    """
    middle=[(a+b)/2 for a,b in zip(edge_a,edge_b)]
    delta=[a-b for a,b in zip(apex,middle)]
    height=math.sqrt(sum(v*v for v in delta));x=[v/height for v in delta]
    edge=[(b-a)/2 for a,b in zip(edge_a,edge_b)]
    projection=sum(a*b for a,b in zip(edge,x))
    tangent=[a-projection*b for a,b in zip(edge,x)]
    half_width=math.sqrt(sum(v*v for v in tangent));y=[v/half_width for v in tangent]
    z=[x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]]
    center=[a+b*height/3 for a,b in zip(middle,x)]
    frame=[[x[i],y[i],z[i],center[i]] for i in range(3)]+[[0,0,0,1]]
    return dict(role=role,primitive='cone',export=True,location=[0,0,0],radius1=1,radius2=1,
                depth=thickness,vertices=3,bevel=0,scale=[2*height/3,2*half_width/math.sqrt(3),1],frame_mm=frame)


def dragon_v2(seed):
    data=dragon(seed).to_dict();data.update(version=2,name='Grounded dragon with continuous folded membranes and an angular face')
    params=data['parameters'];atoms=params['atoms']
    params['atoms']=[a for a in atoms if not a['role'].startswith('membrane_')]
    by_role={a['role']:a for a in params['atoms']}
    replacements={
        'head':ellipsoid('head',[0,-4.05,9.4],[2.15,2.65,1.65]),
        'snout':taper('snout',[0,-4.45,9.26],[0,-6.05,8.97],.92,.54,depth=.70,vertices=4),
        'jaw':cube('jaw',[0,-5.17,8.58],[1.37,2.36,.50],.16),
    }
    for role,atom in replacements.items():
        atom['export']=True;by_role[role].clear();by_role[role].update(atom)
    for side in (-1,1):
        by_role[f'eye_{side}']['dimensions']=[.22,.34,.22]
        by_role[f'eye_socket_{side}']['dimensions']=[.45,.62,.42]
        by_role[f'brow_{side}'].update(start=[side*.65,-4.98,9.77],end=[side*1.01,-3.94,10.03],radius=.29)
        by_role[f'nostril_{side}'].update(location=[side*.4,-5.93,9.16],dimensions=[.3,.4,.28])
        wrist=[side*4.6,.4,10.35];root=[side*1.42,.9,4.65]
        for i in range(3):
            end=[side*(5.95-i*.35),2.8+i*1.12,8.7-i*1.65]
            params['atoms'].append(triangle_membrane(f'membrane_{side}_{i}',root,wrist,end))
        fang=taper(f'jaw_horn_{side}',[side*.68,-4.35,8.65],[side*.9,-3.8,8.05],.25,.13)
        fang['export']=True;params['atoms'].append(fang)
    by_role['lip_recess'].update(location=[0,-5.7,8.76],dimensions=[2.5,1.65,.17])
    params['output_note']='Wing panels are thick triangular-prism primitives spanning body root, wrist and fingers; they overlap at their roots.'
    data['output_roles']=[a['role'] for a in params['atoms'] if a['export']]
    return validate_part(ComponentDefinition.from_dict(data))


def crew_arms_v2(seed):
    data=character_arms('crew',seed).to_dict();data.update(version=2,name='Artillery crew arms reaching down to the loading mechanism')
    p=data['parameters']
    for side,drop in ((1,1.55),(-1,1.35)):
        grip=p['landmarks']['right_grip' if side==1 else 'left_grip'];grip[2]-=drop
        for a in p['atoms']:
            if a['role']==f'forearm_{side}':a['end'][2]-=drop
            if a['role'] in (f'palm_{side}',f'thumb_{side}') or a['role'].startswith(f'finger_{side}_'):a['location'][2]-=drop
    return validate_part(ComponentDefinition.from_dict(data))


def chariot_reins(seed):
    atoms=[]
    for side in (-1,1):
        points=[[side*.88,.7,8.15],[side*1.25,-2.5,6.25],[side*2.65,-8.85,7.12]]
        for i,(a,b) in enumerate(zip(points,points[1:])):atoms.append(link(f'rein_{side}_{i}',a,b,.38))
    return definition('chariot-reins',atoms,seed,notes='Driver-to-bit reins on the two-horse team; bridges remain a print-review concern.')


def loader_bolt(seed):
    a=[-1.65,-1.12,-.96];b=[2.15,-1.34,-1.50]
    return definition('loader-bolt',[link('spare_bolt',a,b,.32),
        taper('spare_bolt_tip',b,[2.95,-1.39,-1.61],.45,.14,vertices=4)],seed,
        notes='Spare bolt rests through the two loading hands; a removable support decision has not been evaluated.')


def dragon_v3(seed):
    data=dragon_v2(seed).to_dict();data.update(version=3,name='Grounded dragon with fitted continuous wing membranes')
    for atom in data['parameters']['atoms']:
        if not atom['role'].startswith('membrane_'):continue
        # Blender's three-sided cone begins at +Y, so map +Y to the apex axis.
        old=atom['frame_mm']
        atom['frame_mm']=[[-old[i][1],old[i][0],old[i][2],old[i][3]] for i in range(3)]+[[0,0,0,1]]
        atom['scale'][0],atom['scale'][1]=atom['scale'][1],atom['scale'][0]
    data['parameters']['native_triangle_apex_axis']='Y'
    return validate_part(ComponentDefinition.from_dict(data))


def all_parts(seed=SEED):
    return _first_pass_parts(seed)+[dragon_v2(seed),dragon_v3(seed),crew_arms_v2(seed),chariot_reins(seed),loader_bolt(seed)]
