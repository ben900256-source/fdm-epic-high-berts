"""Broad planar shield relief assembled from elliptical primitive strokes."""
from copy import deepcopy

from .elves_v2 import identity
from .spearman_overhangs import finish


def flat_seahorse(definitions):
    source = definitions['aurelian.readable-insignia-trial@2']
    data = deepcopy(source.to_dict())
    data.update(version=3, name='Flat broad seahorse shield relief')
    # Shield @2 has a planar front at Y=-0.52. Embed the back 0.12 mm
    # into that face and expose just 0.20 mm (0.26 mm at print scale).
    front, back = -.72, -.40
    atoms, operations = [], []
    landmarks = {'mount': [0, 0, 0]}
    for old in source.to_dict()['parameters']['atoms']:
        if old['role'].endswith('_underside'):
            continue
        role = old['role']
        prior = old['frame_mm']
        frame = identity()
        for i in range(3):
            frame[i][:3] = [prior[i][0], prior[i][2], -prior[i][1]]
            frame[i][3] = prior[i][3]
        frame[0][3] *= .90
        frame[1][3] = (front + back) / 2
        # A cylinder's circular section becomes an ellipse in the shield plane;
        # its caps form a common flat face across every joined stroke.
        width = max(.48, old['dimensions'][0] * 1.12)
        atom = dict(role=role, primitive='cone', location=[0, 0, 0],
                    frame_mm=frame, radius1=1, radius2=1, depth=back-front,
                    scale=[width/2, old['dimensions'][2]/2, 1],
                    vertices=64, bevel=.035, bevel_segments=2, export=not atoms)
        if atoms:
            operations.append(dict(target=atoms[0]['role'], operand=role,
                                   operation='UNION', solver='EXACT'))
        atoms.append(atom)
        landmarks[role] = [frame[i][3] for i in range(3)]
    data['parameters'] = dict(
        atoms=atoms, operations=operations, landmarks=landmarks, seed=1001,
        flat_relief=dict(source=source.reference, source_sha256=source.sha256,
                         shield='aurelian.shield@2', shield_front_y_mm=-.52,
                         front_y_mm=front, back_y_mm=back, relief_mm=.20,
                         embedded_mm=.12, minimum_stroke_width_mm=.48,
                         print_scale=1.3, status='visual-only'))
    return finish(data)


def raised_flat_seahorse(definitions):
    source = definitions['aurelian.readable-insignia-trial@3']
    data = deepcopy(source.to_dict())
    data.update(version=4, name='Flat broad seahorse with stronger raised relief')
    p = data['parameters']
    # Grow only toward the viewer; keep the embedded back and XZ silhouette.
    for atom in p['atoms']:
        atom['depth'] += .10
        atom['frame_mm'][1][3] -= .05
    for role, landmark in p['landmarks'].items():
        if role != 'mount':
            landmark[1] -= .05
    p['flat_relief'].update(source=source.reference, source_sha256=source.sha256,
                            front_y_mm=-.82, relief_mm=.30)
    return finish(data)


def build(figures, definitions, *, raised=False):
    part = raised_flat_seahorse(definitions) if raised else flat_seahorse(definitions)
    prefix = 'raised-flat-seahorse' if raised else 'flat-seahorse'
    specs, gallery = [], []
    for index, original in enumerate(figures, 1):
        spec = deepcopy(original)
        spec.update(assembly_id=f'{prefix}-infantry-{index}-trial',
                    label=f'{"Raised flat" if raised else "Flat"} seahorse shield, pose {index} (visual-only)')
        for placement in spec['placements']:
            if placement['instance_id'].endswith('/shield-insignia'):
                placement.update(part=part.reference, definition_sha256=part.sha256)
            q = deepcopy(placement)
            q['mount'][0][3] += (index-3)*10
            gallery.append(q)
        specs.append(spec)
    specs.append(dict(schema_version=1, assembly_id=f'{prefix}-infantry-gallery-trial',
                      label=('Raised flat' if raised else 'Flat')+' seahorse shields on current infantry (visual-only)', placements=gallery))
    comparison = []
    for source, offset, group in ((figures[2], -4, 'before'), (specs[2], 4, 'after')):
        for placement in source['placements']:
            q = deepcopy(placement)
            q['instance_id'] = group+'/'+q['instance_id'].split('/')[-1]
            q['mount'][0][3] += offset
            comparison.append(q)
    specs.append(dict(schema_version=1, assembly_id=f'{prefix}-infantry-comparison-trial',
                      label=('Low / raised flat seahorse comparison (visual-only)' if raised else
                             'Projecting / flat seahorse comparison (visual-only)'), placements=comparison))
    return part, specs
