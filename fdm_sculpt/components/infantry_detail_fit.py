"""Primitive revisions for sergeant details and supported fist undersides."""
from copy import deepcopy
import math

from .elves_v2 import identity, point
from .spearman_overhangs import finish


def helmet(definitions, seed, version=3):
    source = definitions['aurelian.sergeant-helmet@2']
    parent = definitions['aurelian.helmet@7']
    data = deepcopy(parent.to_dict())
    data.update(component_id=source.component_id, version=version,
                name='Winged sergeant helmet with flush nape and capped feather tips')
    p = data['parameters']
    additions = deepcopy(source.to_dict()['parameters']['atoms'][4:])
    for atom in additions:
        p['atoms'].append(atom)
        if '_wing_feather_' in atom['role']:
            if version >= 4:
                atom['dimensions'][:2] = [.80, .85]
            matrix = atom['frame_mm']
            center = point(matrix, atom['location'])
            vertical_radius = math.sqrt(sum((matrix[2][i] * atom['dimensions'][i] / 2)**2
                                            for i in range(3)))
            top = center[2] + .72 * vertical_radius
            cap = dict(role=atom['role']+'_tip_limit', primitive='cube', export=False,
                       dimensions=[12,12,12], location=[0,0,top-6], bevel=0)
            p['atoms'].append(cap)
            p['operations'].append(dict(target=atom['role'], operand=cap['role'],
                                         operation='INTERSECT', solver='EXACT'))
        p['operations'].append(dict(target='helmet_crown', operand=atom['role'],
                                     operation='UNION', solver='EXACT'))
    p.update(seed=seed, parent=dict(reference=parent.reference, definition_sha256=parent.sha256),
             detail_source=dict(reference=source.reference, definition_sha256=source.sha256),
             feather_tip_height_fraction=.72,
             provenance='Standard infantry revision 7 flush nape retained. Swept wing feathers keep their roots and broad silhouette; horizontal Exact caps remove their vanishing needle ends. Visual-only, pending sliced-detail review.')
    p['landmarks']['wing_roots'] = source.to_dict()['parameters']['landmarks']['wing_roots']
    if version >= 4:
        p['feather_stock_mm'] = [.80, .85]
        p['provenance'] += ' Feather stock broadened after the 0.25 mm slice omitted intermediate tip contours; terminal sections are approximately 0.55 mm across.'
    return finish(data)


def hawk(definitions, seed):
    source = definitions['aurelian.hunting-hawk@2']
    data = deepcopy(source.to_dict())
    data.update(version=3, name='Perched hawk with sturdy shanks and attached talons')
    p = data['parameters']
    for atom in p['atoms']:
        role = atom['role']
        if role.endswith('_leg'):
            atom.update(radius=.38, bevel=.02)
            atom['start'][2] = -.04
        elif role.endswith('_foot'):
            atom['dimensions'] = [.76,.80,.34]
        elif '_toe_' in role:
            atom.update(radius=.13, bevel=.02)
    p.update(seed=seed, detail_source=dict(reference=source.reference, definition_sha256=source.sha256),
             shank_diameter_mm=.76,
             provenance='Broaden both shanks to 0.76 mm and embed their roots into the glove. Feet and attached talons are enlarged locally; body, head and perched pose are preserved. Visual-only, pending sliced-detail review.')
    return finish(data)


def fist(source, version, seed):
    data = deepcopy(source.to_dict())
    data.update(version=version, name=source.name+' with tapered fist underside')
    p = data['parameters']
    forearm = next(a for a in p['atoms'] if a['role']=='cloth_forearm')
    cuff = point(forearm['frame_mm'], [0,0,forearm['depth']/2])
    # Start inside the cloth cuff and open upward at less than 45 degrees.
    # Intersection removes the projecting flat lower corners; the unchanged
    # upper grip, palm orientation and equipment landmarks remain in place.
    bottom = cuff[2] - .35
    height = 5.0
    role = 'fist_rising_envelope'
    p['atoms'].append(dict(role=role, primitive='cone', export=False,
                           location=[cuff[0],cuff[1],bottom+height/2],
                           depth=height, radius1=.35, radius2=.35+.85*height,
                           vertices=64, bevel=0, scale=[1,1,1]))
    hands = [a['role'] for a in p['atoms'] if a['export'] and
             any(term in a['role'] for term in ('palm','fingers','thumb','falconry_glove'))]
    for hand in hands:
        p['operations'].append(dict(target=hand, operand=role, operation='INTERSECT', solver='EXACT'))
    p.update(seed=seed, fist_fit=dict(source=source.reference, source_sha256=source.sha256,
             cuff=cuff, root_z_mm=bottom, root_radius_mm=.35, lateral_growth_per_height=.85),
             provenance=p['provenance']+' Flat projecting fist undersides are clipped to an upward-expanding cuff envelope. Grip and held-item alignment preserved. Visual-only.')
    return finish(data)


def revised_parts(definitions, manifest, seed):
    if type(seed) is not int or seed != manifest['seed']:
        raise ValueError('seed must match the pinned infantry detail manifest')
    for ref, sha in manifest['sources'].items():
        if definitions[ref].sha256 != sha:
            raise ValueError('pinned infantry detail source changed')
    return [helmet(definitions, seed, manifest.get('helmet_version',3)), hawk(definitions, seed),
            *(fist(definitions[p['source']], p['version'], seed) for p in manifest['hands'])]
