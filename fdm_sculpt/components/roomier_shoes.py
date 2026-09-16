"""Larger shoe footprints with local Exact clearance beneath the skirt edging."""
from copy import deepcopy

from .spearman_overhangs import finish

CLEARANCE = .10
SOLE_WIDTH = 1.12
SOLE_LENGTH = 2.35
TOE_WIDTH = 1.08
TOE_LENGTH = 2.04


def revised_parts(definitions, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    result = []
    for suffix in ('', '-b', '-c', '-d', '-e'):
        trim = definitions[f'aurelian.mail-skirt-trim{suffix}@6']
        edging = {a['role']:a for a in trim.to_dict()['parameters']['atoms']}
        for side in ('left', 'right'):
            source = f'aurelian.{side}-leg{suffix}@4'
            data = deepcopy(definitions[source].to_dict())
            data.update(version=5, name=f'{side.title()} leg with roomier fitted shoe')
            p = data['parameters']
            atoms = {a['role']:a for a in p['atoms']}
            sole, toe = atoms[side+'_sole'], atoms[side+'_toe']
            for atom, width, length in ((sole, SOLE_WIDTH, SOLE_LENGTH), (toe, TOE_WIDTH, TOE_LENGTH)):
                # Grow forward from the existing heel, without changing stance.
                atom['location'][1] -= (length-atom['dimensions'][1])/2
                atom['dimensions'][:2] = [width, length]
            toe['dimensions'][2] = .52
            toe['location'][2] -= .03  # Keep the bottom at its reviewed height.
            for atom in (sole, toe):
                frame = atom['frame_mm']
                p['landmarks'][atom['role']] = [sum(frame[i][j]*atom['location'][j] for j in range(3))+frame[i][3] for i in range(3)]

            hem = edging['hem_trim']
            lo = hem['location'][2]-hem['depth']/2-CLEARANCE
            hi = hem['location'][2]+hem['depth']/2+CLEARANCE

            def extended_cone(role, source_atom, z0, z1, radial_pad):
                copy = deepcopy(source_atom)
                bottom = source_atom['location'][2]-source_atom['depth']/2
                slope = (source_atom['radius2']-source_atom['radius1'])/source_atom['depth']
                copy.update(role=role, export=False, depth=z1-z0,
                            location=[0, 0, (z0+z1)/2],
                            radius1=source_atom['radius1']+slope*(z0-bottom)+radial_pad,
                            radius2=source_atom['radius1']+slope*(z1-bottom)+radial_pad)
                return copy

            outer = extended_cone('shoe_trim_clearance', hem, lo, hi, CLEARANCE)
            inner = extended_cone('shoe_trim_clearance_inner', edging['hem_inner'], lo-.10, hi+.10, -CLEARANCE)
            front = deepcopy(edging['front_trim'])
            front.update(role='shoe_front_band_clearance', export=False,
                         dimensions=[v+2*CLEARANCE for v in front['dimensions']])
            p['atoms'].extend([outer, inner, front])
            p['operations'].append(dict(target=outer['role'], operand=inner['role'], operation='DIFFERENCE', solver='EXACT'))
            for target in (side+'_sole', side+'_toe'):
                for cutter in (outer, front):
                    p['operations'].append(dict(target=target, operand=cutter['role'], operation='DIFFERENCE', solver='EXACT'))
            p['shoe_fit'] = dict(source=source, seed=seed, trim_reference=trim.reference,
                                trim_definition_sha256=trim.sha256, clearance_mm=CLEARANCE,
                                sole_width_mm=SOLE_WIDTH, sole_length_mm=SOLE_LENGTH,
                                toe_width_mm=TOE_WIDTH, toe_length_mm=TOE_LENGTH)
            p['boot_style'] = 'Broader, longer forefoot with preserved heel and a recessed seat beneath the skirt edging.'
            p['provenance'] = 'Revision 4 legs retained; shoe footprint enlarged and local trim-envelope clearance cut with Exact CSG. Visual-only.'
            result.append(finish(data))
    return result
