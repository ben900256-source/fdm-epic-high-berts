"""Seat the fuller head farther under the helmet and restore the prior nose."""
from copy import deepcopy

from .spearman_overhangs import finish


def revised_part(definitions):
    source = definitions['aurelian.readable-head-trial@4']
    prior = definitions['aurelian.readable-head-trial@3']
    data = deepcopy(source.to_dict())
    data.update(version=5, name='Fuller head seated farther inside helmet; prior nose profile')
    p = data['parameters']
    prior_atoms = {a['role']: a for a in prior.to_dict()['parameters']['atoms']}
    for atom in p['atoms']:
        if 'frame_mm' in atom:
            atom['frame_mm'][1][3] += .22
        elif 'location' in atom:
            atom['location'][1] += .22
        if atom['role'] == 'nose_bridge':
            restored = deepcopy(prior_atoms['nose_bridge'])
            restored['frame_mm'][1][3] += .22
            atom.clear(); atom.update(restored)
    for landmark in p['landmarks'].values():
        if isinstance(landmark, list) and len(landmark) == 3:
            landmark[1] += .22
    prior_landmarks = prior.to_dict()['parameters']['landmarks']
    for key in ('nose_bridge', 'nose_lower_tip', 'nose_upper_attachment'):
        p['landmarks'][key] = list(prior_landmarks[key])
        p['landmarks'][key][1] += .22
    p['recessed_face'] = dict(source=source.reference, source_sha256=source.sha256,
        nose_source=prior.reference, nose_source_sha256=prior.sha256,
        rearward_shift_mm=.22, print_scale=1.3, seed=1001, status='visual-only')
    p['face_style']['nose'] = 'prior accepted long nose profile, seated farther under helmet'
    chin = next(a for a in p['atoms'] if a['role']=='chin_contour')
    chin['dimensions'] = [.88, .78, .58]
    for role in ('left_cheek_hollow','right_cheek_hollow'):
        cheek=next(a for a in p['atoms'] if a['role']==role)
        cheek['dimensions'][0] *= 1.08
    p['face_style']['silhouette'] = 'sharper cheek-to-jaw taper with a more dragon-like brow and muzzle'
    return finish(data)


def apply(spec, part):
    for placement in spec['placements']:
        if placement['part'] == 'aurelian.readable-head-trial@4':
            placement.update(part=part.reference, definition_sha256=part.sha256)
    spec['label'] = spec.get('label', spec['assembly_id'])+'; recessed head and prior nose (visual-only)'
