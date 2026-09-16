"""Cape-embedded edging, a shorter hem ramp, and centered shoulder mounts."""
from copy import deepcopy

from .elves_v2 import point
from .garment_trims import cape_fitted_mail_trim
from .spearman_overhangs import finish


def revised_parts(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    result = []
    for suffix in ('', '-b', '-c', '-d', '-e'):
        cape = definitions[f'aurelian.cape{suffix}@4']
        data = cape_fitted_mail_trim(cape, seed=seed, revision=7).to_dict()
        data.update(version=8, name='Mail edging embedded into the grounded cape')
        params = data['parameters']
        for atom in params['atoms']:
            if atom['role'].startswith('cape_contact_'):
                atom['frame_mm'][1][3] += .11
            elif atom['role'] == 'cape_rear_limit':
                atom['location'][1] = -2.90  # Rear edge now reaches Y=1.10.
        params['cape_contact_overlap_mm'] = .15
        params['fit_source'] = f'aurelian.mail-skirt-trim{suffix}@6'
        params['provenance'] = 'Rear edging extends 0.60 mm farther back; cape cutout offset 0.15 mm to leave embedded contact. Visual-only.'
        result.append(finish(data))

    data = deepcopy(definitions['aurelian.skirt@7'].to_dict())
    data.update(version=8, name='Mail skirt with foot-level lower taper')
    params = data['parameters']
    atom = next(a for a in params['atoms'] if a['role'] == 'hem_ground_transition')
    old_bottom = atom['location'][2]-atom['depth']/2
    top = atom['location'][2]+atom['depth']/2
    bottom = -5.15
    atom['radius1'] += (atom['radius2']-atom['radius1'])*(bottom-old_bottom)/atom['depth']
    atom.update(depth=top-bottom, location=[0, 0, (top+bottom)/2])
    params['fit_source'] = 'aurelian.skirt@7'
    params['hem_fit'] = dict(seed=seed, lower_cut_mm=bottom-old_bottom, bottom_local_mm=bottom)
    params['provenance'] = 'Lower transition shortened by 0.70 mm, preserving the upper boundary and taper slope. Visual-only.'
    result.append(finish(data))
    return result


def center_shoulders(assembly, definitions):
    """Translate sleeves to their plate armhole centers; reuse cached geometry."""
    result = deepcopy(assembly)
    placements = {p['instance_id']:p for p in result['placements']}
    for name, pad in placements.items():
        if not name.endswith(('/left-tunic', '/right-tunic')):
            continue
        prefix, slot = name.rsplit('/', 1)
        side = slot.split('-')[0]
        plate = placements[prefix+'/mail']
        anchors = definitions[plate['part']].to_dict()['parameters']['landmarks']
        if side+'_armhole' not in anchors:
            continue
        target = point(plate['mount'], anchors[side+'_armhole'])
        source = point(pad['mount'], definitions[pad['part']].to_dict()['parameters']['landmarks'][side+'_pauldron'])
        for axis in range(3):
            pad['mount'][axis][3] = round(pad['mount'][axis][3]+target[axis]-source[axis], 9)
    return result
