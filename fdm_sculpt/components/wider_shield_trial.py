"""Broader shields for the five latest glue-in infantry poses."""
from copy import deepcopy
from math import hypot

from .spearman_overhangs import finish


def build(figures, definitions):
    source = definitions['aurelian.shield@2']
    data = deepcopy(source.to_dict())
    data.update(version=6, name='Twelve percent wider pointed shield')
    p = data['parameters']
    factor = 1.12
    for atom in p['atoms']:
        if atom['role'] == 'shield':
            atom['dimensions'][0] *= factor
        else:
            # Stretch the cutting plane in X, then renormalize its frame.
            # Keep rigid frames and the original bottom height.
            m = atom['frame_mm']
            nx, nz = m[0][2]/factor, m[2][2]
            length = hypot(nx, nz)
            nx, nz = nx/length, nz/length
            m[0][0], m[2][0] = nz, -nx
            m[0][2], m[2][2] = nx, nz
            m[0][3] *= factor
    p['wider_shield_trial'] = dict(source=source.reference, source_sha256=source.sha256,
                                   width_factor=factor, print_scale=1.3, seed=1001,
                                   status='visual-only')
    part = finish(data)
    specs, gallery = [], []
    for i, original in enumerate(figures, 1):
        spec = deepcopy(original)
        spec.update(assembly_id=f'wider-shield-infantry-{i}-trial',
                    label=f'Broader shield, pose {i} (visual-only)')
        for placement in spec['placements']:
            if placement['instance_id'].endswith('/shield'):
                placement.update(part=part.reference, definition_sha256=part.sha256)
            q = deepcopy(placement)
            q['mount'][0][3] += (i-3)*10
            gallery.append(q)
        specs.append(spec)
    specs.append(dict(schema_version=1, assembly_id='wider-shield-infantry-gallery-trial',
                      label='Five broader-shield infantry poses (visual-only)', placements=gallery))
    comparison = []
    for source_spec, offset, group in ((figures[2], -4, 'before'), (specs[2], 4, 'after')):
        for placement in source_spec['placements']:
            q = deepcopy(placement)
            q['instance_id'] = group+'/'+q['instance_id'].split('/')[-1]
            q['mount'][0][3] += offset
            comparison.append(q)
    specs.append(dict(schema_version=1, assembly_id='wider-shield-infantry-comparison-trial',
                      label='Original / broader shield (visual-only)', placements=comparison))
    base_source = definitions['aurelian.glue-tray-five-walled@1']
    base_data = deepcopy(base_source.to_dict())
    base_data.update(version=2, name='Five glue recesses spaced for broader infantry')
    bp = base_data['parameters']
    pitch = 7.6
    outside = 4*pitch+5.5+1.6
    for atom in bp['atoms']:
        if atom['role'] == 'tray':
            atom['dimensions'][0] = outside/1.3
        else:
            index = int(atom['role'].split('_')[-1])
            atom['location'][0] = (index-3)*pitch/1.3
    bp['recipe'].update(pitch_mm=pitch, outside_mm=[outside, 8.4, 2],
                        source=base_source.reference, source_sha256=base_source.sha256)
    base = finish(base_data)
    empty = dict(schema_version=1, assembly_id='wider-shield-base-empty-trial',
                 label='Five wider-spaced glue recesses (visual-only)', placements=[dict(
                     instance_id='tray', part=base.reference, definition_sha256=base.sha256,
                     mount=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])])
    row = deepcopy(empty)
    row.update(assembly_id='wider-shield-walled-row-trial',
               label='Broader shields in five glue recesses (visual-only)')
    for i, figure in enumerate(specs[:5], 1):
        for placement in figure['placements']:
            q = deepcopy(placement)
            q['mount'][0][3] += (i-3)*pitch/1.3
            q['mount'][2][3] += .8/1.3
            row['placements'].append(q)
    specs.extend((empty, row))
    return [part, base], specs
