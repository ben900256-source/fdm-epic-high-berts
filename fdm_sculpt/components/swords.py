"""Reusable straight short sword with an exposed hilt, guard and pommel."""
from .core import ComponentDefinition
from .parts import validate_part


def short_sword(*, seed):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    atoms = [
        dict(role='blade_grip', primitive='cylinder', export=True, location=[0,0,0],
             radius=.4, depth=1.9, vertices=40, bevel=.035),
        dict(role='blade_pommel', primitive='sphere', export=False, location=[0,0,-1.02],
             dimensions=[1,.85,.45], segments=32, ring_count=24),
        dict(role='blade_guard', primitive='cube', export=False, location=[0,0,1.00],
             dimensions=[1.85,.8,.3], bevel=.08),
        dict(role='blade_body', primitive='cone', export=False, location=[0,0,2.4],
             radius1=.56, radius2=.48, depth=2.7, vertices=4, scale=[1,.7,1], bevel=.02),
        dict(role='blade_point', primitive='cone', export=False, location=[0,0,4.17],
             radius1=.48, radius2=.12, depth=.90, vertices=4, scale=[1,.7,1], bevel=.015),
    ]
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id='aurelian.shortblade', version=2, name='Longer elven short sword with exposed hilt',
        family='shortblade', required_anchors=['mount'], semantic_slots=['mono'], output_roles=['blade_grip'],
        parameters=dict(atoms=atoms, operations=[dict(target='blade_grip', operand=a['role'],
            operation='UNION', solver='EXACT') for a in atoms[1:]],
            landmarks=dict(mount=[0,0,0], grip=[0,0,0], guard=[0,0,1], tip=[0,0,4.62], pommel=[0,0,-1.02]),
            seed=seed, design=dict(grip_diameter_mm=.8, grip_length_mm=1.9, blade_length_mm=3.57,
                guard_width_mm=1.85, overall_length_mm=5.865,
                note='Broad straight diamond-section blade with a short tapered point; hilt extends above and below the fist.'),
            provenance='Original primitive and ordered Exact short-sword revision; existing grip origin retained. Visual-only.'))))
