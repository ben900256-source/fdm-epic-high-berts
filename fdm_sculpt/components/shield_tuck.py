"""Pose shields against the mail hem with concealed, rising primitive joins."""
from copy import deepcopy

from .elves_v2 import frame, multiply, point, translation
from .spearman_overhangs import finish, ramp


def inverse_rigid(matrix):
    rows = [[matrix[j][i] for j in range(3)] for i in range(3)]
    return [row+[-sum(row[j]*matrix[j][3] for j in range(3))] for row in rows]+[[0,0,0,1]]


def tucked_mount(pose):
    return multiply(pose['shield']['mount'],
                    frame(pose['pivot_shield_mm'], (pose['angle_degrees'],0,0),
                          pose.get('offset_shield_mm',(0,0,0))))


def recessed_join_mount(pose):
    """Move the cached join behind the shield face without rebuilding it."""
    shield = tucked_mount(pose)
    setback = pose.get('join_recess_mm',0)
    return multiply(translation([shield[i][1]*setback for i in range(3)]),
                    pose['connector']['mount'])


def halfspace(role, origin, normal):
    """Positive halfspace represented by an oversized oriented cube."""
    matrix = ramp(role, origin, [a+b for a,b in zip(origin,normal)], 1, 1)['frame_mm']
    for i in range(3):
        matrix[i][3] = origin[i]
    return dict(role=role, primitive='cube', location=[0,0,8], dimensions=[16,16,16],
                frame_mm=matrix, bevel=0, export=False)


def flat_web(data, local, pose, manifest):
    """A flat, tapered backing behind the shield point, grown from the hem."""
    p = data['parameters']
    tip = point(local,(0,-.42,-2.275))
    root = [tip[0],-.95,-5.0]
    rear = point(inverse_rigid(local),root)
    front_y, front_z, top = manifest.get('web_front_y_mm',-.49), -2.34, -1.45
    back, bottom = max(rear[1]+.30,manifest.get('web_min_back_y_mm',-10)), rear[2]-.30
    target = 'concealed_hem_join'
    atoms = [dict(role=target, primitive='cube', export=True, bevel=.025,
                  location=[0,(front_y+back)/2,(bottom+top)/2],
                  dimensions=[1.0,back-front_y,top-bottom])]
    slope = (rear[2]-front_z)/(rear[1]-front_y)
    atoms.extend([
        halfspace('web_rising_underside',[0,front_y,front_z],[0,-slope,1]),
        halfspace('web_left_taper',[-.20,front_y,0],[1,.50,0]),
        halfspace('web_right_taper',[.20,front_y,0],[-1,.50,0]),
    ])
    from .elves_v2 import identity
    for atom in atoms:
        atom['frame_mm'] = multiply(local,atom.get('frame_mm',identity()))
    atoms.append(halfspace('web_hem_floor',[0,0,-5.08],[0,0,1]))
    p['atoms'] = atoms
    p['operations'] = [dict(target=target,operand=a['role'],operation='INTERSECT',solver='EXACT') for a in atoms[1:]]
    p['landmarks'].update(skirt_attachment=root,
                          shield_attachment=point(local,(0,-.20,-1.65)))
    p.pop('diameter_mm')
    p['design'] = dict(pivot_shield_mm=pose['pivot_shield_mm'],
                       inward_angle_degrees=pose['angle_degrees'],
                       offset_shield_mm=pose['offset_shield_mm'],
                       embedded_width_mm=1.0, front_tip_width_mm=.40,
                       style='flat tapered backing; no cone')
    p['provenance'] = 'Near-upright shield moved toward the body. Flat Exact-cut backing rooted inside the mail hem meets the lower tip; tapered sides stay behind the shield. No round cone or ground foot. Visual-only.'
    data['name'] = 'Flat concealed backing for near-upright shield'


def revised_parts(definitions, manifest, seed):
    if type(seed) is not int or seed != manifest['seed']:
        raise ValueError('seed must match the pinned shield tuck manifest')
    result = []
    lower = manifest.get('root_radius_mm', .38)
    upper = manifest.get('upper_radius_mm', .42)
    for pose in manifest['poses']:
        for name in ('shield','insignia','connector','skirt'):
            item = pose[name]
            if definitions[item['part']].sha256 != item['definition_sha256']:
                raise ValueError('pinned shield tuck source changed')
        source = definitions[pose['connector']['part']]
        data = deepcopy(source.to_dict())
        local = multiply(inverse_rigid(pose['connector']['mount']), tucked_mount(pose))
        tip = point(local, (0,-.42,-2.275))
        end = point(local, (0,-.20,-1.65))
        start = [tip[0],-.95,-4.95]
        p = data['parameters']
        p['atoms'] = [ramp('concealed_hem_join', start, end, lower, upper)]
        p['operations'] = []
        p['landmarks'] = dict(mount=[0,0,0], skirt_attachment=start,
                              shield_attachment=end, shield_tip_front=tip)
        p.pop('overhang_revision', None)
        p.update(seed=seed, diameter_mm=2*lower,
                 tuck_source=source.reference, tuck_source_sha256=source.sha256,
                 shield_mount=tucked_mount(pose),
                 design=dict(pivot_shield_mm=pose['pivot_shield_mm'],
                             inward_angle_degrees=pose['angle_degrees'],
                             root_radius_mm=lower, upper_radius_mm=upper),
                 provenance='Permanent tapered join rooted inside the existing mail hem, beneath the inward-tucked shield point. Replaces the elevated round lower connector; no ground foot or removable support. Visual-only.')
        data.update(version=manifest.get('version',3), name='Concealed mail hem to tucked shield join')
        if manifest.get('join_style') == 'flat_web':
            flat_web(data,local,pose,manifest)
        result.append(finish(data))
    return result
