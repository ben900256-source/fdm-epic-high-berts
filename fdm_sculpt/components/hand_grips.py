"""Rotate a primitive fist at its existing grip without moving the arm pose."""
import math
from .core import ComponentDefinition
from .elves_v2 import identity, multiply, translation
from .parts import validate_part


def align_hand(source, revision, direction):
    length = math.sqrt(sum(v*v for v in direction))
    if not math.isfinite(length) or length < 1e-8:
        raise ValueError('grip direction must be finite and nonzero')
    x, y, z = [v/length for v in direction]
    if z < -.999999:
        raise ValueError('choose the opposite direction for a downward grip')
    # Rodrigues shortest rotation from the fist Z axis to the grip tangent.
    k = [[0, 0, x], [0, 0, y], [-x, -y, 0]]
    r = identity()
    for i in range(3):
        for j in range(3):
            r[i][j] += k[i][j]+sum(k[i][n]*k[n][j] for n in range(3))/(1+z)
    data = source.to_dict()
    data['version'] = revision
    data['name'] += ' with aligned fist'
    p = data['parameters']
    grip = p['landmarks']['grip']
    frame = multiply(translation(grip), multiply(r, translation([-v for v in grip])))
    for atom in p['atoms']:
        if atom['role'].endswith(('_palm', '_fingers', '_thumb')):
            atom['frame_mm'] = multiply(frame, atom.get('frame_mm', identity()))
    p['landmarks']['grip_axis'] = [x, y, z]
    p['grip_alignment'] = dict(parent_reference=source.reference, parent_sha256=source.sha256,
                               direction=[x,y,z])
    p['provenance'] = 'Reviewed shoulder, elbow and grip position preserved; fist aligned to local horn tangent with primitive frames. Visual-only.'
    return validate_part(ComponentDefinition.from_dict(data))
