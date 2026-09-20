"""A visual study of bolder infantry detail at the accepted print height."""
from copy import deepcopy
from math import cos, sin, pi, sqrt

from .core import ComponentDefinition
from .elves_v2 import identity, multiply, point
from .parts import validate_part
from .upper_spear_trial import fill_part


def yaw(pivot, degrees):
    a = degrees*pi/180
    turn = [[cos(a),-sin(a),0,0],[sin(a),cos(a),0,0],[0,0,1,0],[0,0,0,1]]
    for axis in range(3):
        turn[axis][3] = pivot[axis]-sum(turn[axis][j]*pivot[j] for j in range(3))
    return turn


def finish(data, source):
    p = data['parameters']
    p['detail_trial'] = dict(source=source.reference, source_sha256=source.sha256,
                             seed=1001, print_scale=1.3, status='visual-only')
    data['output_roles'] = [a['role'] for a in p['atoms'] if a['export']]
    return validate_part(ComponentDefinition.from_dict(data))


def revised_parts(definitions):
    parts = []
    for ref, name in [('aurelian.torso@4', 'torso'), ('aurelian.chest-plate@4', 'chest-plate')]:
        source = definitions[ref]
        data = deepcopy(source.to_dict())
        data.update(component_id=f'aurelian.readable-{name}-trial', version=1,
                    name='Broader infantry '+name)
        for atom in data['parameters']['atoms']:
            atom['dimensions'][0] *= 1.15
            atom['location'][0] *= 1.15
        for landmark in data['parameters']['landmarks'].values():
            landmark[0] *= 1.15
        data['parameters']['width_factor'] = 1.15
        parts.append(finish(data, source))

    source = definitions['aurelian.head@12']
    data = deepcopy(source.to_dict())
    data.update(component_id='aurelian.readable-head-trial', version=1,
                name='Elven face with deeper eyes, mouth and stronger nose')
    p = data['parameters']
    for atom in p['atoms']:
        role = atom['role']
        if role.endswith('eye_socket'):
            atom['dimensions'] = [.52, .76, .30]
            atom['frame_mm'][2][3] = .32
            p['landmarks'][role][2] = .32
        elif role == 'mouth_line':
            atom['dimensions'] = [.72, .50, .24]
        elif role == 'nose_bridge':
            atom['dimensions'] = [.42, .68, .90]
            atom['frame_mm'][1][3] -= .10
            for key in ('nose_bridge', 'nose_lower_tip', 'nose_upper_attachment'):
                p['landmarks'][key][1] -= .10
        elif role == 'chin_contour':
            atom['dimensions'] = [.88, .80, .54]
    p['face_style'].update(mouth='broader, deeper single groove', eyes='enlarged angled recesses',
                           nose='long nose with stronger forward projection')
    parts.append(finish(data, source))

    source = definitions['aurelian.skirt@8']
    data = deepcopy(source.to_dict())
    data.update(component_id='aurelian.readable-mail-trial', version=1,
                name='Coarse interlocking mail with broader upper skirt')
    p = data['parameters']
    p['atoms'] = [a for a in p['atoms'] if a['role'] in ('mail_skirt_backing', 'hem_ground_transition')]
    backing = p['atoms'][0]
    backing['radius2'] = 1.10
    p['operations'] = []
    centers = []
    # Coarse oval relief, with solid backing retained behind each recessed eye.
    # Seven staggered rows replace thirteen; sixteen links replace thirty.
    for row in range(7):
        z = -4.49 + row*.57
        radius = 1.55 + (1.10-1.55)*(z+4.85)/4.35
        for col in range(16):
            angle = 2*pi*(col+.5*(row%2))/16
            nx, ny = cos(angle), sin(angle)/.75
            length = sqrt(nx*nx+ny*ny)
            nx, ny = nx/length, ny/length
            center = [radius*cos(angle)+.06*nx, radius*.75*sin(angle)+.06*ny, z]
            frame = [[ny,nx,0,center[0]],[-nx,ny,0,center[1]],[0,0,1,z],[0,0,0,1]]
            role = f'mail_link_{row}_{col}'
            p['atoms'].extend([
                dict(role=role, primitive='sphere', dimensions=[.65,.54,.70],
                     frame_mm=frame, location=[0,0,0], segments=24, ring_count=16, export=True),
                dict(role=role+'_eye', primitive='sphere', dimensions=[.29,.85,.32],
                     frame_mm=deepcopy(frame), location=[0,.12,0], segments=20, ring_count=14, export=False)])
            p['operations'].append(dict(target=role, operand=role+'_eye', operation='DIFFERENCE', solver='EXACT'))
            centers.append(center)
    p['chainmail'] = dict(rows=7, links_per_row=16, staggered=True, centers_local=centers,
                          outer_mm=[.65,.54,.70], eye_mm=[.29,.85,.32])
    parts.append(finish(data, source))

    source = definitions['aurelian.shield-insignia@4']
    data = deepcopy(source.to_dict())
    data.update(component_id='aurelian.readable-insignia-trial', version=1,
                name='Seahorse with stronger relief and broad strokes')
    p = data['parameters']
    for atom in p['atoms']:
        frame = deepcopy(atom.get('frame_mm', identity()))
        center = point(frame, atom['location'])
        center[1] = -.17 + (center[1]+.17)*1.45
        for axis in range(3):
            frame[axis][3] = center[axis]
        atom.update(frame_mm=frame, location=[0,0,0])
        if 'dimensions' in atom:
            atom['dimensions'][1] *= 1.45
            atom['dimensions'][0] *= 1.18
        else:
            atom['scale'][1] *= 1.45
            atom['scale'][0] *= 1.18
    for key, landmark in p['landmarks'].items():
        if key != 'mount':
            landmark[1] = -.17 + (landmark[1]+.17)*1.45
    p['relief_update'] = dict(depth_factor=1.45, stroke_width_factor=1.18, fixed_back_plane_mm=-.17)
    parts.append(finish(data, source))
    return parts


def build(figures, definitions):
    parts = revised_parts(definitions)
    replacements = dict(zip(('torso','mail','head','skirt','shield-insignia'), parts))
    specs, gallery = [], []
    fixed = {'footing','terrain','left-leg','right-leg','skirt','skirt-trim','cape','waist-wrap'}
    for index, (source, degrees, head_turn, shield_turn) in enumerate(zip(
            figures, (-16,14,0,-12,18), (12,-16,0,18,-12), (-10,12,0,-12,10)), 1):
        spec = deepcopy(source)
        spec.update(assembly_id=f'readable-infantry-{index}-trial',
                    label=f'Broader infantry and bold detail, pose {index} (visual-only)')
        torso = next(p for p in source['placements'] if p['instance_id'].endswith('/torso'))
        pivot = [r[3] for r in torso['mount'][:3]]
        turn = yaw(pivot, degrees)
        for placement in spec['placements']:
            slot = placement['instance_id'].split('/')[-1]
            if slot in replacements:
                part = replacements[slot]
                placement.update(part=part.reference, definition_sha256=part.sha256)
            if slot not in fixed:
                placement['mount'] = multiply(turn, placement['mount'])
        slots = {p['instance_id'].split('/')[-1]:p for p in spec['placements']}
        look = yaw([r[3] for r in slots['head']['mount'][:3]], head_turn)
        shoulder = point(slots['left-arm']['mount'], definitions[slots['left-arm']['part']].to_dict()['parameters']['landmarks']['left_shoulder_slope'])
        guard = yaw(shoulder, shield_turn)
        for slot in ('head','helmet','crest'):
            slots[slot]['mount'] = multiply(look, slots[slot]['mount'])
        for slot in ('left-arm','shield','shield-insignia','shield-torso-connector','shield-lower-connector'):
            slots[slot]['mount'] = multiply(guard, slots[slot]['mount'])
        # Refit the shoulder/helmet join after changing head direction.
        fill = fill_part(spec, definitions, index).to_dict()
        fill.update(component_id=f'aurelian.readable-helmet-fill-{index}-trial', version=1)
        fill = validate_part(ComponentDefinition.from_dict(fill))
        parts.append(fill)
        slots['helmet-spear-fill'].update(part=fill.reference, definition_sha256=fill.sha256, mount=identity())
        for placement in spec['placements']:
            q = deepcopy(placement)
            q['mount'][0][3] += (index-3)*10
            gallery.append(q)
        specs.append(spec)
    specs.append(dict(schema_version=1, assembly_id='readable-infantry-gallery-trial',
                      label='Broader infantry / bold detail study (visual-only, source scale)', placements=gallery))
    # A direct same-pose comparison separates detail/proportion changes from pose.
    comparison = []
    for source, offset, prefix in ((figures[2],-4,'before'),(specs[2],4,'after')):
        for placement in source['placements']:
            q = deepcopy(placement)
            q['instance_id'] = prefix+'/'+q['instance_id'].split('/')[-1]
            q['mount'][0][3] += offset
            comparison.append(q)
    specs.append(dict(schema_version=1, assembly_id='readable-infantry-comparison-trial',
                      label='Printed design / bolder detail comparison (visual-only)', placements=comparison))
    return parts, specs
