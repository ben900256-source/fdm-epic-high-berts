"""A wider face and clearer helmet aperture, retaining the helmet silhouette."""
from copy import deepcopy

from .spearman_overhangs import finish


def revised_parts(definitions):
    source = definitions['aurelian.readable-head-trial@2']
    data = deepcopy(source.to_dict())
    data.update(version=3, name='Broader face with stronger eye and mouth recesses')
    p = data['parameters']
    for atom in p['atoms']:
        role = atom['role']
        if role in ('cranium', 'head_envelope', 'chin_contour'):
            atom['dimensions'][0] *= 1.10
        elif role.endswith('cheek_hollow'):
            atom['location'][0] *= 1.10
        elif role.endswith('eye_socket'):
            atom['dimensions'] = [.62, .88, .36]
            atom['frame_mm'][0][3] = -.34 if role.startswith('left') else .34
        elif role == 'mouth_line':
            atom['dimensions'] = [.82, .62, .28]
            atom['location'][1] = -.82
    for name, landmark in p['landmarks'].items():
        if name.endswith('cheek_hollow'):
            landmark[0] *= 1.10
        elif name.endswith('eye_socket'):
            landmark[0] = -.34 if name.startswith('left') else .34
        elif name == 'mouth_line':
            landmark[1] = -.82
    p['face_style'].update(eyes='wider and taller angled recesses with deeper floors',
                           mouth='wider and deeper single groove', cranium='10 percent broader oval')
    p['clear_face_trial'] = dict(source=source.reference, source_sha256=source.sha256,
                                head_width_factor=1.10, print_scale=1.3, seed=1001,
                                status='visual-only')
    head = finish(data)

    source = definitions['aurelian.helmet@7']
    data = deepcopy(source.to_dict())
    data.update(component_id='aurelian.readable-helmet-trial', version=1,
                name='Original helmet outline with broader face opening')
    p = data['parameters']
    for atom in p['atoms']:
        if atom['role'] == 'helmet_face_opening':
            atom['dimensions'] = [1.20, 2.3, 1.86]
            atom['bevel'] = .08
        elif atom['role'] == 'nape_front_clearance':
            atom['dimensions'][0] = 1.20
    p['landmarks']['front_brim'][2] = .74
    p['clear_face_trial'] = dict(source=source.reference, source_sha256=source.sha256,
                                opening_mm=[1.20, 1.86], outer_atoms_unchanged=True,
                                print_scale=1.3, seed=1001, status='visual-only')
    return head, finish(data)


def build(figures, definitions):
    parts = revised_parts(definitions)
    replacements = dict(zip(('head', 'helmet'), parts))
    specs, gallery = [], []
    for index, original in enumerate(figures, 1):
        spec = deepcopy(original)
        spec.update(assembly_id=f'clear-face-infantry-{index}-trial',
                    label=f'Broader face and clearer helmet opening, pose {index} (visual-only)')
        for placement in spec['placements']:
            slot = placement['instance_id'].split('/')[-1]
            if slot in replacements:
                part = replacements[slot]
                placement.update(part=part.reference, definition_sha256=part.sha256)
            q = deepcopy(placement)
            q['mount'][0][3] += (index-3)*10
            gallery.append(q)
        specs.append(spec)
    specs.append(dict(schema_version=1, assembly_id='clear-face-infantry-gallery-trial',
                      label='Broader faces and open helmets (visual-only)', placements=gallery))
    comparison = []
    for source, offset, group in ((figures[2], -4, 'before'), (specs[2], 4, 'after')):
        for placement in source['placements']:
            q = deepcopy(placement)
            q['instance_id'] = group+'/'+q['instance_id'].split('/')[-1]
            q['mount'][0][3] += offset
            comparison.append(q)
    specs.append(dict(schema_version=1, assembly_id='clear-face-infantry-comparison-trial',
                      label='Current / broader clearer face (visual-only)', placements=comparison))
    return parts, specs
