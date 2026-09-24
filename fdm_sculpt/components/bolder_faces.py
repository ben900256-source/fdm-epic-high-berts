"""Slightly fuller heads and deeper facial relief, with fixed assembly mounts."""
from copy import deepcopy
from .elves_v2 import point
from .spearman_overhangs import finish

SOURCES = (
    'aurelian.readable-head-trial@3',
    'aurelian.readable-helmet-trial@1',
    'aurelian.sergeant-helmet-accepted-r6@1',
    'aurelian.swordmaster-sergeant-helmet-accepted-r2@1',
    'aurelian.dragon-prince-helmet-accepted-r6@1',
)


def revised_parts(definitions):
    parts = {}
    for ref in SOURCES:
        source = definitions[ref]
        data = deepcopy(source.to_dict())
        data.update(version=source.version + 1, name=source.name+' - fuller face detail')
        p = data['parameters']
        p['bolder_face'] = dict(source=ref, source_sha256=source.sha256,
            width_factor=1.08, depth_factor=1.05, height_factor=1.0,
            seed=1001, print_scale=1.3, status='visual-only')
        head = ref == SOURCES[0]
        for a in p['atoms']:
            role = a['role']
            if role in ('cranium', 'head_envelope', 'chin_contour',
                        'helmet_crown', 'nape_ellipsoid'):
                a['dimensions'][0] *= 1.08
                a['dimensions'][1] *= 1.05
            elif role in ('dragon_crown', 'helmet_tapered_tip'):
                a.setdefault('scale', [1, 1, 1])[0] *= 1.08
                a['scale'][1] *= 1.05
            elif role.endswith('cheek_hollow'):
                a['location'][0] *= 1.08
                p['landmarks'][role] = list(a['location'])
            elif role.endswith('eye_socket'):
                a['dimensions'] = [.70, 1.06, .42]
                a['frame_mm'][0][3] = -.375 if role.startswith('left') else .375
                a['frame_mm'][1][3] = -.86
                p['landmarks'][role] = point(a['frame_mm'], a['location'])
            elif role == 'nose_bridge':
                a['dimensions'] = [.49, .86, 1.00]
                a['frame_mm'][1][3] = -.99
                p['landmarks']['nose_bridge'] = point(a['frame_mm'], [0, 0, 0])
                p['landmarks']['nose_lower_tip'] = point(a['frame_mm'], [0, 0, -.50])
                p['landmarks']['nose_upper_attachment'] = point(a['frame_mm'], [0, 0, .50])
            elif role == 'mouth_line':
                a['dimensions'] = [.88, .70, .30]
                a['location'][1] = -.86
                p['landmarks'][role] = list(a['location'])
            elif role in ('helmet_face_opening', 'face_opening'):
                a['dimensions'] = [1.34, 2.50, 1.98]
                a['bevel'] = .06
            elif role == 'nape_front_clearance':
                a['dimensions'][0:2] = [1.34, 2.50]
        if head:
            p['face_style'].update(cranium='8 percent wider, 5 percent fuller; unchanged height',
                eyes='broader angled sockets with deeper floors',
                nose='stronger long bridge, retaining the rising underside envelope')
        elif ref == SOURCES[1]:
            p['landmarks']['front_brim'][2] = .80
        part = finish(data)
        parts[ref] = part
    return parts


def apply(spec, parts):
    """Only replace the pinned head/helmet definitions; never move a figure."""
    for placement in spec['placements']:
        part = parts.get(placement['part'])
        if part:
            placement.update(part=part.reference, definition_sha256=part.sha256)
    spec['label'] = spec.get('label', spec['assembly_id'])+'; bolder faces (visual-only)'
