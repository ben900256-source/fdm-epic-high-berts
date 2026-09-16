"""Pose-specific cloth arms, made only from primitives and ordered local Exact CSG."""
from copy import deepcopy
import math

from .cloth_robes import ellipsoid, operation
from .elves_v2 import identity, point
from .spearman_overhangs import finish, ramp


def add(a, b):
    return [x+y for x, y in zip(a, b)]


def scale(v, factor):
    return [x*factor for x in v]


def between(a, b, t):
    return [x+(y-x)*t for x, y in zip(a, b)]


def unit(v):
    length = math.sqrt(sum(x*x for x in v))
    return scale(v, 1/length)


def hand_atom(atom):
    return any(token in atom['role'] for token in
               ('palm', 'fingers', 'thumb', 'knuckle_plate', 'falconry_glove'))


def pose(source):
    p = source.to_dict()['parameters']
    marks = p['landmarks']
    if 'shoulder' in marks:
        shoulder, elbow, grip = (marks[k] for k in ('shoulder', 'elbow', 'grip'))
        direction = unit([g-e for g, e in zip(grip, elbow)])
        wrist = add(grip, scale(direction, -.24))
    else:
        upper = next(a for a in p['atoms'] if a['role'].endswith('_upper_arm'))
        side = upper['role'].split('_')[0]
        shoulder = point(upper.get('frame_mm', identity()), upper['start'])
        elbow, wrist = marks[side+'_elbow'], marks[side+'_cuff']
    return shoulder, elbow, wrist


def robe_arm(source, version, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    if type(version) is not int or version <= source.version:
        raise ValueError('cloth arms require a new positive revision')
    data = deepcopy(source.to_dict())
    old = data['parameters']
    shoulder, elbow, wrist = pose(source)
    upper_axis = unit([e-s for s, e in zip(shoulder, elbow)])
    root = 'robe_sleeve'
    # One garment follows both limb segments. The shoulder is narrow and seated
    # in the existing armhole; the fullness is below it, around the bent elbow.
    body = ramp(root, shoulder, elbow, .39, .53)
    body.update(bevel=.08, bevel_segments=3)
    p = dict(atoms=[body], operations=[], landmarks=deepcopy(old['landmarks']),
             seed=seed, robe_source=source.reference,
             robe_source_sha256=source.sha256,
             cloth_pose=dict(shoulder=shoulder, elbow=elbow, wrist=wrist),
             provenance='Continuous posed robe sleeve with elbow fullness, tension folds and gathered wrist. Original hands and mounts retained. Visual-only.')

    def join(atom, kind='UNION'):
        atom['export'] = False
        p['atoms'].append(atom)
        p['operations'].append(operation(root, atom['role'], kind))

    join(ellipsoid('cloth_shoulder', add(shoulder, scale(upper_axis, -.19)),
                   add(shoulder, scale(upper_axis, .43)), .79, .79))
    forearm = ramp('cloth_forearm', elbow, wrist, .53, .33)
    forearm.update(bevel=.07, bevel_segments=3)
    join(forearm)
    join(dict(role='cloth_elbow', primitive='sphere', location=add(elbow,[0,0,-.08]),
              dimensions=[1.04,1.04,1.12], segments=32, ring_count=24))
    # A soft drape across the inside of the bend replaces the exposed joint.
    join(ellipsoid('elbow_drape', add(between(shoulder,elbow,.67),[0,0,-.12]),
                   add(between(elbow,wrist,.42),[0,0,-.12]), .72, .72))
    # Broad tapering folds, rather than ornamental scratches or metal bands.
    # Each segment defines its own radial frame, so raised arms carry their folds.
    for segment, start, end, r0, r1 in (
            ('upper', shoulder, elbow, .39, .53),
            ('fore', elbow, wrist, .53, .33)):
        frame = ramp('axis', start, end, 1, 1)['frame_mm']
        def surface(t, angle, inset):
            radius = r0+(r1-r0)*t+inset
            radial = [radius*(frame[i][0]*math.cos(angle)+frame[i][1]*math.sin(angle))
                      for i in range(3)]
            return add(between(start,end,t),radial)
        for i in range(4):
            angle = (i+.22)*math.pi/2
            join(ellipsoid(f'{segment}_cloth_fold_{i}', surface(.13,angle,-.07),
                           surface(.88,angle+.22,-.06), .29, .29))
            join(ellipsoid(f'{segment}_cloth_valley_{i}', surface(.23,angle+.52,.015),
                           surface(.81,angle+.64,.015), .16, .16), 'DIFFERENCE')
    # Retain the sculpted grips exactly, including enlarged horn hands and glove.
    for atom in old['atoms']:
        if hand_atom(atom):
            atom = deepcopy(atom)
            atom['export'] = True
            p['atoms'].append(atom)
    data.update(version=version, name=source.name+' — posed robe arm', parameters=p)
    return finish(data)


def revised_parts(definitions, manifest, seed):
    if seed != manifest['seed']:
        raise ValueError('seed must match the pinned pose manifest')
    parts = []
    for record in manifest['sources']:
        source = definitions[record['source']]
        if source.sha256 != record['definition_sha256']:
            raise ValueError('source pose definition changed: '+source.reference)
        parts.append(robe_arm(source,record['version'],seed))
    return parts


def fitted_bow_shoulders(definitions, seed):
    """Seat the forward/elevated archer sleeves in the side-on robe body."""
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    result=[]
    for suffix,version in (('',3),('-elevated-20',2),('-elevated-30',2),('-elevated-40',2)):
        source=definitions[f'aurelian.archer-bow-arm{suffix}@{version}']
        data=deepcopy(source.to_dict())
        p=data['parameters']
        shoulder=p['cloth_pose']['shoulder']
        # The original small shoulder dome stopped short of the rotated tunic.
        # This inset cloth yoke is inside the body at one end, retaining the
        # narrow outer shoulder and preserving every hand and limb landmark.
        inner=[shoulder[0],shoulder[1]+.43,shoulder[2]-.10]
        yoke=ramp('cloth_inset_yoke',inner,shoulder,.34,.39)
        yoke.update(export=False,bevel=.07,bevel_segments=3)
        p['atoms'].append(yoke)
        p['operations'].append(operation('robe_sleeve',yoke['role']))
        p['shoulder_fit_source']=source.reference
        p['shoulder_fit_source_sha256']=source.sha256
        p['seed']=seed
        data.update(version=version+1,name=source.name+' with inset cloth shoulder')
        result.append(finish(data))
    return result
