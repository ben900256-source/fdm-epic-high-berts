"""A broad faceted leaf spearhead on the reviewed uniform shaft."""
from copy import deepcopy

from .spearman_overhangs import finish


def decorative_spear(definitions):
    source = definitions['aurelian.uniform-spear-140-trial@1']
    data = deepcopy(source.to_dict())
    data.update(version=2, name='Uniform spear with broad faceted leaf blade')
    p = data['parameters']
    # Four-sided elliptical sections create a diamond section and a strong
    # central ridge on both faces. The lower shoulder grows gradually upward.
    lower = dict(role='spear_leaf_lower', primitive='cone', export=False,
                 location=[0, .46, 7.755], radius1=.48, radius2=1.20,
                 depth=1.25, scale=[1, .50, 1], vertices=4, bevel=0)
    tip = dict(role='spear_leaf_tip', primitive='cone', export=False,
               location=[0, .46, 9.525], radius1=1.20, radius2=.27,
               depth=2.35, scale=[1, .50, 1], vertices=4, bevel=0)
    replacements = {a['role']: a for a in (lower, tip)}
    p['atoms'] = [replacements.get(a['role'], a) for a in p['atoms']]
    p['operations'].extend(dict(target='spear', operand=a['role'], operation='UNION', solver='EXACT')
                           for a in (lower, tip))
    p['landmarks'].update(spear_leaf_lower=lower['location'], spear_leaf_tip=tip['location'],
                          blade_shoulder=[0, .46, 8.38], blade_terminal=[0, .46, 10.70])
    p['decorative_blade'] = dict(source=source.reference, source_sha256=source.sha256,
                                width_mm=2.40, depth_mm=1.20, root_z_mm=7.13,
                                shoulder_z_mm=8.38, tip_z_mm=10.70,
                                terminal_width_mm=.54, terminal_depth_mm=.27,
                                print_scale=1.3, seed=1001, status='visual-only',
                                style='Broad leaf silhouette with diamond section and central ridge',
                                note='Small flat terminal cap; shaft, grip and collar unchanged')
    return finish(data)


def thicker_decorative_spear(definitions):
    source = definitions['aurelian.uniform-spear-140-trial@2']
    data = deepcopy(source.to_dict())
    data.update(version=3, name='Uniform spear with fuller faceted leaf blade')
    p = data['parameters']
    for atom in p['atoms']:
        if atom['role'] in ('spear_leaf_lower', 'spear_leaf_tip'):
            atom['scale'][1] *= 1.15
    p['decorative_blade'].update(source=source.reference, source_sha256=source.sha256,
                                depth_mm=1.38, terminal_depth_mm=.3105,
                                thickness_factor=1.15,
                                note='15 percent thicker front-to-back; outline, length, shaft and collar unchanged')
    return finish(data)


def build(figures, definitions, *, thicker=False):
    part = thicker_decorative_spear(definitions) if thicker else decorative_spear(definitions)
    prefix = 'fuller-spear' if thicker else 'decorative-spear'
    specs, gallery = [], []
    for index, original in enumerate(figures, 1):
        spec = deepcopy(original)
        spec.update(assembly_id=f'{prefix}-infantry-{index}-trial',
                    label=f'{"Fuller faceted" if thicker else "Faceted"} leaf spearhead, pose {index} (visual-only)')
        for placement in spec['placements']:
            if placement['instance_id'].endswith('/spear'):
                placement.update(part=part.reference, definition_sha256=part.sha256)
            q = deepcopy(placement)
            q['mount'][0][3] += (index-3)*10
            gallery.append(q)
        specs.append(spec)
    specs.append(dict(schema_version=1, assembly_id=f'{prefix}-infantry-gallery-trial',
                      label=('Fuller' if thicker else 'Broad')+' faceted leaf spearheads (visual-only)', placements=gallery))
    comparison = []
    for source, offset, group in ((figures[2], -4, 'before'), (specs[2], 4, 'after')):
        for placement in source['placements']:
            q = deepcopy(placement)
            q['instance_id'] = group+'/'+q['instance_id'].split('/')[-1]
            q['mount'][0][3] += offset
            comparison.append(q)
    specs.append(dict(schema_version=1, assembly_id=f'{prefix}-infantry-comparison-trial',
                      label=('Original / fuller faceted spearhead (visual-only)' if thicker else
                             'Blunt / faceted leaf spearhead (visual-only)'), placements=comparison))
    return [part], specs
