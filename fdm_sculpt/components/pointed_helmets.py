"""Restore the pointed upper helmet and fit a higher, broader front crest."""
from copy import deepcopy
from math import sqrt

from .elves_v2 import point, identity
from .spearman_overhangs import finish

# Keep the face opening and lower rim fixed. Lengthen the upper silhouette to
# add 20% of the original 3.8 mm overall height above the brow.
BROW_Z = .80
UPPER_FACTOR = 1.475
HELMETS = (
    'aurelian.readable-helmet-trial',
    'aurelian.sergeant-helmet-accepted-r6',
    'aurelian.swordmaster-sergeant-helmet-accepted-r2',
)


def stretch_vertical(atom, rise=0):
    """Scale an upright primitive about the brow, retaining rigid transforms."""
    center = point(atom.get('frame_mm', identity()), atom['location'])
    center[2] = BROW_Z + (center[2]-BROW_Z)*UPPER_FACTOR + rise
    # Shell and crest envelopes are upright; the tapered cut is handled below.
    frame = atom.get('frame_mm')
    if frame:
        assert all(abs(frame[i][j]-(1 if i==j else 0)) < 1e-8
                   for i in range(3) for j in range(3))
        atom.pop('frame_mm')
    atom['location'] = center
    if 'dimensions' in atom:
        atom['dimensions'][2] *= UPPER_FACTOR
    if 'depth' in atom:
        atom['depth'] *= UPPER_FACTOR


def revised_parts(definitions):
    replacements = {}
    for component_id in HELMETS:
        source = definitions[component_id+'@2']
        data = deepcopy(source.to_dict())
        data.update(version=4, name=source.name+' - restored tall pointed crown')
        p = data['parameters']
        for atom in p['atoms']:
            if atom['role'] in ('helmet_crown', 'helmet_tapered_tip'):
                stretch_vertical(atom)
        p['landmarks']['helmet_crown'] = [0, .08, -.38]
        p['landmarks']['helmet_tapered_tip'] = [0, .08, 2.49625]
        p['landmarks']['point_top'] = [0, .08, 3.16]
        p['pointed_helmet'] = dict(source=source.reference, source_sha256=source.sha256,
            brow_z=BROW_Z, upper_factor=UPPER_FACTOR, overall_height_factor=1.20,
            nominal_top_z=3.16, opening_and_nape_unchanged=True,
            seed=1001, print_scale=1.3, status='visual-only')
        replacements[component_id+'@3'] = finish(data)

    source = definitions['aurelian.crest@4']
    data = deepcopy(source.to_dict())
    data.update(version=6, name='High broad triangular crest fitted to the pointed crown')
    p = data['parameters']
    for atom in p['atoms']:
        role = atom['role']
        if role == 'crest_lower_taper':
            # Preserve the sloping underside, seated higher over the brow.
            atom['frame_mm'][1][3] = -.93
            atom['frame_mm'][2][3] = .94
            continue
        if role.endswith('_front'):
            continue
        stretch_vertical(atom, rise=.16)
        if role in ('helmet_leaf_crest', 'helmet_crest_spine',
                    'helmet_leaf_crest_inner', 'helmet_crest_spine_inner'):
            atom['dimensions'][0] *= 1.08
            atom['dimensions'][1] *= 1.05
            atom['location'][1] -= .08
        elif role == 'helmet_leaf_crest_outline':
            atom['radius1'] *= 1.35
            atom['radius2'] *= 1.35
            atom['bevel'] = .08
        elif role == 'helmet_crest_spine_outline':
            atom['dimensions'][0] *= 1.35
    # Root the thin raised spine in the leaf, which in turn overlaps the shell.
    inner = next(a for a in p['atoms'] if a['role']=='helmet_crest_spine_inner')
    inner['dimensions'][1] -= .10
    p['landmarks'].update(crest_center=[0,-.73,1.8745], stripe_center=[0,-.73,1.8745],
        lower_taper_start=[0,-.93,.94], lower_taper_front=[0,-1.10,1.11])
    p['pointed_crest'] = dict(source=source.reference, source_sha256=source.sha256,
        upper_factor=UPPER_FACTOR, rise_mm=.16, outline_width_factor=1.35,
        forward_shift_mm=.08, seed=1001, print_scale=1.3, status='visual-only')
    crest = finish(data)
    backed = deepcopy(crest.to_dict())
    backed.update(version=7, name=crest.name+' - solid fitted backing')
    backing = backed['parameters']
    backing['operations'] = [op for op in backing['operations']
        if not (op['target']=='helmet_leaf_crest' and op['operation']=='DIFFERENCE')]
    backing['pointed_crest'].update(backing_source=crest.reference,
        backing_source_sha256=crest.sha256,
        backing='Solid leaf volume extends inward through the helmet surface')
    crest = finish(backed)
    replacements['aurelian.crest@4'] = crest
    replacements['aurelian.crest@5'] = crest
    # Join the upper cone to the crown at its actual ellipsoid radius.
    for previous_ref, part in list(replacements.items()):
        if part.family != 'helmet':
            continue
        data = deepcopy(part.to_dict())
        data.update(version=5, name=part.name+' - continuous taper')
        p = data['parameters']
        crown = next(a for a in p['atoms'] if a['role']=='helmet_crown')
        tip = next(a for a in p['atoms'] if a['role']=='helmet_tapered_tip')
        join, top = 2.35, 3.16
        rx, ry, rz = [v/2 for v in crown['dimensions']]
        root = rx*sqrt(1-((join-crown['location'][2])/rz)**2)
        tip.update(location=[0,.08,(join+top)/2], depth=top-join,
                   radius1=root, radius2=.12, scale=[1,ry/rx,1],
                   rotation=[0,0,0], bevel=.025)
        p['landmarks']['helmet_tapered_tip'] = list(tip['location'])
        p['pointed_helmet'].update(transition_source=part.reference,
            transition_source_sha256=part.sha256, tangent_join_z=join,
            nominal_terminal_diameter=.24)
        replacements[previous_ref] = finish(data)
    return replacements


def apply(spec, replacements):
    for placement in spec['placements']:
        part = replacements.get(placement['part'])
        if part:
            placement.update(part=part.reference, definition_sha256=part.sha256)
