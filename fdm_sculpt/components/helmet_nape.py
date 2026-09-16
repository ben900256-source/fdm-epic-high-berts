"""Flush lower helmet transition built from primitive frusta and Exact CSG."""
from copy import deepcopy
import math

from .spearman_overhangs import finish, cone

ROOT_Z = -1.4
JOIN_Z = -.55
ROOT_RADIUS = .38
Y_SCALE = 1 / .82
SEGMENTS = 24


def profile(z):
    """Hermite radius, tangent to the approved elliptical crown at the join."""
    length = JOIN_Z - ROOT_Z
    t = (z - ROOT_Z) / length
    end = .82 * math.sqrt(1 - (JOIN_Z / 2.2) ** 2)
    slope = -.82 * JOIN_Z / (2.2 ** 2 * math.sqrt(1 - (JOIN_Z / 2.2) ** 2))
    return ((2*t**3-3*t**2+1)*ROOT_RADIUS + (t**3-2*t**2+t)*length*.70
            + (-2*t**3+3*t**2)*end + (t**3-t**2)*length*slope)


def segmented_parts_v6(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    helmet = deepcopy(definitions['aurelian.helmet@5'].to_dict())
    helmet.update(version=6, name='Helmet with flush curved nape')
    p = helmet['parameters']
    p['provenance'] = ('Revision 5 upper crown, cap and face opening retained. Lower nape '
                       'is a tangent profile clipped to the original crown envelope, locally '
                       'fused into the helmet instead of a separate torso collar. Visual-only.')
    p['nape_profile'] = dict(root_z=ROOT_Z, join_z=JOIN_Z, root_radius=ROOT_RADIUS,
                             root_slope=.70, segments=SEGMENTS, seed=seed)
    p['atoms'][2]['location'][2] = 7.2 + JOIN_Z + 2
    p['landmarks']['helmet_nape_clip'][2] = JOIN_Z + 2
    p['landmarks']['nape_root'] = [0, .08, ROOT_Z]
    p['landmarks']['nape_join'] = [0, .08, JOIN_Z]
    envelope = deepcopy(p['atoms'][0])
    envelope.update(role='nape_envelope', export=False)
    p['atoms'].append(envelope)
    operations = [p['operations'][0]]
    for i in range(SEGMENTS):
        lo = ROOT_Z + (JOIN_Z-ROOT_Z)*i/SEGMENTS
        hi = ROOT_Z + (JOIN_Z-ROOT_Z)*(i+1)/SEGMENTS
        # Small volume overlaps remove coplanar-only joins. The envelope clips
        # their outer edges to the original helmet surface at the upper seam.
        lo -= .002 if i else 0
        hi += .02 if i == SEGMENTS-1 else .002
        atom = cone(f'nape_band_{i:02}', [0, .08, (lo+hi)/2], hi-lo,
                    profile(lo), profile(hi), [1, Y_SCALE, 1])
        atom.update(export=False, vertices=64)
        p['atoms'].append(atom)
        if i:
            operations.append(dict(target='nape_band_00', operand=atom['role'],
                                   operation='UNION', solver='EXACT'))
    operations.extend([
        dict(target='nape_band_00', operand='nape_envelope', operation='INTERSECT', solver='EXACT'),
        dict(target='helmet_crown', operand='nape_band_00', operation='UNION', solver='EXACT'),
        *p['operations'][1:],
        dict(target='helmet_crown', operand='nape_front_clearance', operation='DIFFERENCE', solver='EXACT'),
    ])
    p['atoms'].append(dict(role='nape_front_clearance', primitive='cube',
                           location=[0, -.95, -1.50], dimensions=[1.08, 2.3, 1.20],
                           bevel=0, export=False))
    p['operations'] = operations
    torso = deepcopy(definitions['aurelian.torso@2'].to_dict())
    torso.update(version=4, name='Torso for integrated helmet nape')
    torso['parameters']['provenance'] = ('Revision 2 torso restored: the separate revision 3 '
                                        'nape transition now belongs to helmet revision 6.')
    return [finish(helmet), finish(torso)]


def ellipse_parameters():
    radius = profile(JOIN_Z)
    derivative = -.82*JOIN_Z/(2.2**2*math.sqrt(1-(JOIN_Z/2.2)**2))
    distance = JOIN_Z-ROOT_Z
    k = derivative/radius
    q = distance**2/(1-(ROOT_RADIUS/radius)**2-2*k*distance)
    offset = -k*q
    z_radius = math.sqrt(q+offset**2)
    return radius*z_radius/math.sqrt(q), z_radius, JOIN_Z-offset


def revised_parts(definitions, seed):
    """One analytic ellipsoid avoids nearly coincident frustum seams in Exact."""
    _, torso = segmented_parts_v6(definitions, seed)
    helmet = deepcopy(definitions['aurelian.helmet@5'].to_dict())
    helmet.update(version=7, name='Helmet with flush elliptical nape')
    p = helmet['parameters']
    rx, rz, center = ellipse_parameters()
    p['atoms'][2]['location'][2] = 7.2+JOIN_Z+2
    p['landmarks']['helmet_nape_clip'][2] = JOIN_Z+2
    p['landmarks']['nape_root'] = [0, .08, ROOT_Z]
    p['landmarks']['nape_join'] = [0, .08, JOIN_Z]
    p['atoms'].extend([
        dict(role='nape_ellipsoid', primitive='sphere', export=False,
             dimensions=[2*rx, 2*rx*Y_SCALE, 2*rz], location=[0, .08, center],
             segments=64, ring_count=96),
        dict(role='nape_limits', primitive='cube', export=False, bevel=0,
             dimensions=[4, 4, JOIN_Z+.10-ROOT_Z], location=[0, 0, (ROOT_Z+JOIN_Z+.10)/2]),
        dict(role='nape_front_clearance', primitive='cube', export=False, bevel=0,
             dimensions=[1.08, 2.3, 1.20], location=[0, -.95, -1.50]),
    ])
    p['operations'] = [
        p['operations'][0],
        dict(target='nape_ellipsoid', operand='nape_limits', operation='INTERSECT', solver='EXACT'),
        dict(target='helmet_crown', operand='nape_ellipsoid', operation='UNION', solver='EXACT'),
        *p['operations'][1:],
        dict(target='helmet_crown', operand='nape_front_clearance', operation='DIFFERENCE', solver='EXACT'),
    ]
    p['provenance'] = ('Revision 5 crown and cap retained above the lower join. A single '
                       'ellipsoid matches the crown radius and tangent at the nape. '
                       'Replaces the segmented revision 6 preview after a face-cut artifact. Visual-only.')
    p['nape_profile'] = dict(root_z=ROOT_Z, join_z=JOIN_Z, root_radius=ROOT_RADIUS,
                             radius_x=rx, radius_z=rz, center_z=center, seed=seed)
    return [finish(helmet), torso]
