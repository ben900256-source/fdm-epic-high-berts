"""Local primitive revisions for the upright spearman overhang study.

The recipes retain the reviewed sources and mounts. These are permanent
transitions, not removable supports, and do not establish print readiness.
"""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .parts import validate_part


def revision(definitions, reference, version, note):
    data = deepcopy(definitions[reference].to_dict())
    data['version'] = version
    data['name'] += ' - tapered undersides'
    data['parameters']['overhang_revision'] = dict(source=reference, intent=note)
    return data


def finish(data):
    data['output_roles'] = [a['role'] for a in data['parameters']['atoms'] if a['export']]
    return validate_part(ComponentDefinition.from_dict(data))


def cone(role, location, depth, lower, upper, scale=(1, 1, 1)):
    return dict(role=role, primitive='cone', location=list(location), depth=depth,
                radius1=lower, radius2=upper, scale=list(scale), vertices=48,
                bevel=0, export=True)


def ramp(role, start, end, lower, upper):
    """Circular frustum along a segment, with a rigid local frame."""
    delta = [b-a for a, b in zip(start, end)]
    length = math.sqrt(sum(v*v for v in delta))
    z = [v/length for v in delta]
    axis = [0, 1, 0] if abs(z[1]) < .9 else [1, 0, 0]
    x = [axis[1]*z[2]-axis[2]*z[1], axis[2]*z[0]-axis[0]*z[2], axis[0]*z[1]-axis[1]*z[0]]
    norm = math.sqrt(sum(v*v for v in x))
    x = [v/norm for v in x]
    y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]]
    atom = cone(role, (0, 0, 0), length, lower, upper)
    atom['frame_mm'] = [[x[i], y[i], z[i], (start[i]+end[i])/2] for i in range(3)]+[[0, 0, 0, 1]]
    return atom


def revised_parts(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    results = []
    torso = revision(definitions, 'aurelian.torso@2', 3,
                     'Widen the rear collar gradually under the helmet nape; keep the face clear.')
    torso['parameters']['atoms'].append(cone('nape_transition', (0, .22, .94), 1.24, .44, .86, (1, 1.04, 1)))
    results.append(finish(torso))

    skirt = revision(definitions, 'aurelian.skirt@3', 6,
                     'Grow the mail hem from a terrain-embedded tapered lower band.')
    skirt['parameters']['atoms'].append(cone('hem_ground_transition', (0, 0, -5.175), 1.05, .98, 1.68, (1, .75, 1)))
    results.append(finish(skirt))

    spear = revision(definitions, 'aurelian.spear@3', 4,
                     'Match blade depth across its widest shoulder and lengthen socket and blade root ramps.')
    atoms = {a['role']: a for a in spear['parameters']['atoms']}
    atoms['spear_leaf_lower'].update(depth=1.0, location=[1.05, -.76, 13.28], scale=[1, .85, 1])
    atoms['spear_collar_ramp'].update(depth=.60, location=[0, .46, 6.85])
    results.append(finish(spear))

    shield = revision(definitions, 'aurelian.shield@2', 3,
                      'Extend a narrow tapered shoe from the lower point into the terrain.')
    shoe = cone('shield_ground_transition', (0, 0, -2.70), 1.25, .18, .76, (.35, 1, 1))
    shoe.update(vertices=4, rotation=[0, 0, math.pi/4])
    shield['parameters']['atoms'].append(shoe)
    results.append(finish(shield))

    insignia = revision(definitions, 'aurelian.shield-insignia@2', 3,
                        'Back the lower edge of each relief stroke with a shallow tapered transition into the shield.')
    additions = []
    for atom in insignia['parameters']['atoms']:
        if not atom['export'] or atom['primitive'] != 'sphere':
            continue
        frame = atom.get('frame_mm', [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
        location = atom['location']
        center = [sum(frame[i][j]*location[j] for j in range(3))+frame[i][3] for i in range(3)]
        radii = [math.sqrt(sum((frame[i][j]*atom['dimensions'][j]/2)**2 for j in range(3))) for i in range(3)]
        h = radii[2]+.20
        backing = cone(atom['role']+'_underside', (center[0], center[1]+.055, center[2]-h/2+.03),
                       h, .05, 1, (radii[0]*.96, radii[1], 1))
        additions.append(backing)
    insignia['parameters']['atoms'].extend(additions)
    results.append(finish(insignia))

    for suffix in ('', '-b', '-c', '-d', '-e'):
        arm = revision(definitions, f'aurelian.right-arm{suffix}@1', 2,
                       'Grow the gripping hand from the elbow with a concealed tapered palm underside.')
        p = arm['parameters']
        elbow, fingers = p['landmarks']['right_elbow'], p['landmarks']['right_grouped_fingers']
        start = [elbow[0], elbow[1], elbow[2]-.30]
        end = [fingers[0], fingers[1]+.10, fingers[2]+.03]
        p['atoms'].append(ramp('grip_underside_transition', start, end, .30, .60))
        results.append(finish(arm))

        for kind, version in (('lower', 2), ('torso', 2)):
            connector = revision(definitions, f'aurelian.shield-{kind}-connector{suffix}@1', version,
                                 'Replace the round hanging underside with a lower angled permanent join.')
            p = connector['parameters']
            original = p['atoms'][0]
            start, end = original['start'], original['end']
            # The root starts inside the skirt/body below the original bar.
            root = [end[0], end[1], min(start[2], end[2])-.95]
            tip = [start[0], start[1], start[2]+.02]
            p['atoms'].append(ramp('connector_lower_transition', root, tip, .30, original['radius']))
            results.append(finish(connector))
    return results


def refined_parts(definitions, seed):
    """Second pass: the sliced hem includes a wider trim than the mail backing."""
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    results = []
    skirt = revision(definitions, 'aurelian.skirt@6', 7,
                     'Continue the ground ramp to the full 1.99 mm radius of the separate hem trim.')
    atom = next(a for a in skirt['parameters']['atoms'] if a['role']=='hem_ground_transition')
    atom.update(location=[0, 0, -5.325], depth=1.05, radius1=1.25, radius2=2.0)
    results.append(finish(skirt))
    shield = revision(definitions, 'aurelian.shield@3', 4,
                      'Reach the full shield thickness before the lower point begins, retaining its broad outline.')
    atom = next(a for a in shield['parameters']['atoms'] if a['role']=='shield_ground_transition')
    atom.update(location=[0, 0, -2.75], depth=1.0, radius1=.22, radius2=.80, scale=[.35, 1.03, 1])
    results.append(finish(shield))
    insignia = revision(definitions, 'aurelian.shield-insignia@3', 4,
                        'Bring each shallow relief ramp up to the full front depth of its stroke.')
    for atom in insignia['parameters']['atoms']:
        if atom['role'].endswith('_underside'):
            atom['scale'][1] += .055
    results.append(finish(insignia))
    for suffix in ('', '-b', '-c', '-d', '-e'):
        arm = revision(definitions, f'aurelian.right-arm{suffix}@2', 3,
                       'Add a vertical palm ramp rooted around the spear grip beneath the grouped fingers.')
        p = arm['parameters']
        fingers = p['landmarks']['right_grouped_fingers']
        p['atoms'].append(cone('fingers_lower_transition',
                               [fingers[0], fingers[1]+.06, fingers[2]-.375],
                               1.15, .35, .76, (1, .70, 1)))
        results.append(finish(arm))
    return results


def sleeve_part(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    sleeve = revision(definitions, 'aurelian.right-tunic@2', 3,
                      'Taper the lower pauldron hem into the arm; the mount points local Z downward.')
    sleeve['parameters']['atoms'].append(cone('sleeve_underside_transition', (0, 0, .65), .60, .52, .18))
    return finish(sleeve)


def deposited_shield_part(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    shield = revision(definitions, 'aurelian.shield@4', 5,
                      'Keep the ground-contact cross-section wide enough to retain a deposited path before the shield starts.')
    atom = next(a for a in shield['parameters']['atoms'] if a['role']=='shield_ground_transition')
    atom.update(location=[0, 0, -2.75], depth=1.10, radius1=.74, radius2=.85, scale=[.45, .90, 1])
    return finish(shield)
