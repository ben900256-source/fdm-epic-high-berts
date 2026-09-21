"""Constant-diameter intact spears with fuller gripping hands."""
from copy import deepcopy

from .spearman_overhangs import finish


def uniform_spear(definitions):
    source = definitions['aurelian.upper-spear-160-trial@1']
    data = deepcopy(source.to_dict())
    data.update(component_id='aurelian.uniform-spear-140-trial', version=1,
                name='Uniform 1.4 mm source spear shaft with matching collar and head')
    p = data['parameters']
    p['atoms'] = [a for a in p['atoms'] if a['role'] not in ('upper_transition', 'upper_shaft')]
    p['operations'] = [o for o in p['operations'] if o['operand'] not in ('upper_transition', 'upper_shaft')]
    for index, atom in enumerate(p['atoms']):
        if atom['role'] == 'spear':
            p['atoms'][index] = dict(role='spear', primitive='cylinder', radius=.70,
                                    depth=13.35, location=[0, .46, .525],
                                    vertices=64, bevel=.03, export=True)
        elif atom['role'] in ('spear_leaf_lower', 'spear_leaf_tip',
                               'spear_collar_ramp', 'spear_collar_band'):
            atom['radius1'] *= .875
            atom['radius2'] *= .875
    p['design'].update(shaft_diameter_mm=1.4, upper_shaft_diameter_mm=1.4,
                       lower_shaft_diameter_mm=1.4, collar_diameter_mm=1.54,
                       note='Constant shaft diameter; no step or enlargement above the hand.')
    p['experiment'] = dict(source=source.reference, source_sha256=source.sha256,
                           print_scale=1.3, printed_upper_diameter_mm=1.82,
                           printed_lower_diameter_mm=1.82, status='visual-only')
    return finish(data)


def fuller_hand(source):
    data = deepcopy(source.to_dict())
    data.update(version=2, name=source.name+' with larger gripping hand')
    p = data['parameters']
    roles = {'right_palm', 'right_grouped_fingers', 'right_thumb', 'right_knuckle_plate'}
    for atom in p['atoms']:
        if atom['role'] in roles:
            atom['dimensions'] = [v*1.25 for v in atom['dimensions']]
            if 'bevel' in atom:
                atom['bevel'] *= 1.25
        elif atom['role'].endswith('_additive_taper'):
            # Grow the hand end, leaving the attachment at the wrist fixed.
            atom['radius2'] *= 1.25
        elif atom['role'] == 'fingers_lower_transition':
            atom['radius2'] *= 1.20
    p['uniform_grip_trial'] = dict(source=source.reference, source_sha256=source.sha256,
                                   hand_dimension_factor=1.25, wrist_root_unchanged=True,
                                   print_scale=1.3, seed=1001, status='visual-only')
    return finish(data)


def build(figures, definitions):
    spear = uniform_spear(definitions)
    parts, specs, gallery = [spear], [], []
    for index, original in enumerate(figures, 1):
        spec = deepcopy(original)
        spec.update(assembly_id=f'uniform-spear-infantry-{index}-trial',
                    label=f'Uniform spear and fuller grip, pose {index} (visual-only)')
        for placement in spec['placements']:
            slot = placement['instance_id'].split('/')[-1]
            if slot == 'right-arm':
                part = fuller_hand(definitions[placement['part']])
                parts.append(part)
            elif slot == 'spear':
                part = spear
            else:
                part = None
            if part is not None:
                placement.update(part=part.reference, definition_sha256=part.sha256)
            q = deepcopy(placement)
            q['mount'][0][3] += (index-3)*10
            gallery.append(q)
        specs.append(spec)
    specs.append(dict(schema_version=1, assembly_id='uniform-spear-infantry-gallery-trial',
                      label='Uniform spears with fuller hands (visual-only)', placements=gallery))
    comparison = []
    for source, offset, group in ((figures[2], -4, 'before'), (specs[2], 4, 'after')):
        for placement in source['placements']:
            q = deepcopy(placement)
            q['instance_id'] = group+'/'+q['instance_id'].split('/')[-1]
            q['mount'][0][3] += offset
            comparison.append(q)
    specs.append(dict(schema_version=1, assembly_id='uniform-spear-infantry-comparison-trial',
                      label='Stepped / uniform spear and fuller grip (visual-only)', placements=comparison))
    return parts, specs
