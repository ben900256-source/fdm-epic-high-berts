"""Give upright spears a visible lean using placements, preserving cached parts."""
from math import acos, atan2, cos, degrees, hypot, radians, sqrt

from .elves_v2 import frame, multiply, point

MINIMUM_LEAN_DEGREES = 6.0


def lean_degrees(mount):
    direction = [row[2] for row in mount[:3]]
    return degrees(atan2(hypot(*direction[:2]), abs(direction[2])))


def apply(spec, definitions):
    """Pivot nearly upright shafts through the existing hand, outward in local X.

    The projected finger landmark fixes the shaft's position within the grip.
    Only its rigid placement changes; hands, joins and component geometry stay
    pinned. Already inclined weapons and historical source recipes are untouched.
    """
    groups = {}
    for placement in spec['placements']:
        if '/' in placement['instance_id']:
            group, slot = placement['instance_id'].split('/', 1)
            groups.setdefault(group, {})[slot] = placement
    records = []
    for group, slots in groups.items():
        if 'spear' not in slots:
            continue
        spear = slots['spear']
        before = lean_degrees(spear['mount'])
        if before >= MINIMUM_LEAN_DEGREES - 1e-6:
            continue
        arm = slots['right-arm']
        landmarks = definitions[arm['part']].to_dict()['parameters']['landmarks']
        fingers = point(arm['mount'], landmarks['right_grouped_fingers'])
        shaft = definitions[spear['part']].to_dict()['parameters']['landmarks']['spear']
        local_axis = [shaft[0], shaft[1], 0.0]
        origin = point(spear['mount'], local_axis)
        direction = [row[2] for row in spear['mount'][:3]]
        length_squared = sum(v*v for v in direction)
        local_axis[2] = sum((a-b)*d for a, b, d in zip(fingers, origin, direction)) / length_squared
        pivot = point(spear['mount'], local_axis)
        # R_y(a) changes the world axis to column Z*cos(a) + column X*sin(a).
        # Solve for exactly six degrees from world Z, preserving the existing
        # fore/aft component rather than replacing the whole pose.
        z = direction[2] / sqrt(length_squared)
        x = spear['mount'][2][0]
        amount = degrees(atan2(x, z) + acos(cos(radians(MINIMUM_LEAN_DEGREES)) / hypot(z, x)))
        spear['mount'] = multiply(spear['mount'], frame(local_axis, (0, amount, 0)))
        records.append(dict(figure=group, before_degrees=before,
                            after_degrees=lean_degrees(spear['mount']),
                            local_pivot_mm=local_axis, grip_axis_pivot_mm=pivot))
    if records:
        spec['spear_lean'] = dict(minimum_degrees=MINIMUM_LEAN_DEGREES,
                                  status='visual-only; angle change not yet printed',
                                  placements=records)
    return records
