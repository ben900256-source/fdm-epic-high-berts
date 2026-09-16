"""Shorten the primitive cape hems without moving their shoulder attachments."""
from copy import deepcopy
from .spearman_overhangs import finish

HEM_RAISE = .575


def revised_parts(definitions, seed, revision=4):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    if revision not in (3,4):
        raise ValueError('unsupported cape hem revision')
    raise_mm = 1.35 if revision == 3 else HEM_RAISE
    parts = []
    for suffix in ('', '-b', '-c', '-d', '-e'):
        source = f'aurelian.cape{suffix}@2'
        data = deepcopy(definitions[source].to_dict())
        data.update(version=revision, name='Cape with hem above terrain' if revision==3 else 'Cape with ground-contact hem')
        p = data['parameters']
        cloak = next(a for a in p['atoms'] if a['role']=='cloak')
        depth = cloak['depth']
        # Preserve the original cone's upper section and slope. This is a
        # shorter primitive, not a translation of the complete garment.
        cloak['radius1'] += (cloak['radius2']-cloak['radius1'])*raise_mm/depth
        cloak['depth'] -= raise_mm
        cloak['location'][2] += raise_mm/2
        frame = cloak['frame_mm']
        p['landmarks']['cloak'] = [sum(frame[i][j]*cloak['location'][j] for j in range(3))+frame[i][3] for i in range(3)]
        p['hem_revision'] = dict(source=source, raise_mm=raise_mm, seed=seed)
        p['provenance'] = (('Revision 2 cape shortened at its hem by 1.35 mm. ' if revision==3 else
                            'Revision 2 cape shortened at its hem by 0.575 mm to meet the ground plane. ')+
                           'Shoulder drapes, upper cone boundary, taper slope and mounts preserved. Visual-only.')
        parts.append(finish(data))
    return parts
