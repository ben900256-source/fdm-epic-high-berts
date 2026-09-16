"""Separate sacrificial shield pedestal candidates; physical calibration pending."""
from .spearman_overhangs import finish


def support_part(seed, neck_depth=.40):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    if neck_depth not in (.30, .40, .50):
        raise ValueError('use a pinned 0.30, 0.40 or 0.50 mm trial neck')
    atoms = []
    for role, size, z in [
        ('pedestal_foot', [.80, .85, .20], -3.24),
        ('base_breakaway_neck', [.55, neck_depth, .40], -3.05),
        ('pedestal_body', [.70, .85, .40], -2.75),
        ('shield_breakaway_neck', [.55, neck_depth, .54], -2.37),
    ]:
        atoms.append(dict(role=role, primitive='cube', dimensions=size,
                          location=[0, 0, z], bevel=0, export=not atoms))
    return finish(dict(component_id=f'aurelian.shield-breakaway-{round(neck_depth*100):02}',
                       version=1, name=f'Shield breakaway pedestal - {neck_depth:.2f} mm neck trial',
                       family='sacrificial-support', required_anchors=['mount'], semantic_slots=['mono'],
                       output_roles=['pedestal_foot'], parameters=dict(
                           atoms=atoms,
                           operations=[dict(target='pedestal_foot', operand=a['role'], operation='UNION',
                                            solver='EXACT') for a in atoms[1:]],
                           landmarks=dict(mount=[0,0,0], upper_cut=[0,0,-2.45], lower_cut=[0,0,-3.03]),
                           trial=dict(seed=seed, neck_depth_mm=neck_depth, neck_width_mm=.55,
                                      removable=True, validated=False, removal='clip upper neck, then lower neck; do not twist shield'),
                           provenance='Independent visual prototype, mounted in shield coordinates. Nominal necks require sliced and physical trials.')))
