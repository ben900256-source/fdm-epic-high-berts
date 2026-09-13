"""Local Exact recesses that keep the bow handle inside the gripping fist."""
from .core import ComponentDefinition
from .parts import validate_part


def fitted_handle(source, revision, *, radius=.40, half_length=.90):
    """Retain the reviewed bow/fitting outside a cylindrical hand-grip region."""
    if radius<.375 or half_length<.8:
        raise ValueError('retain a 0.75 mm handle and cover the entire gripping hand')
    data=source.to_dict()
    data['version']=revision
    data['name']+=' with recessed hand grip'
    p=data['parameters']
    center=p['landmarks']['grip']
    shell='hand_grip_trim_shell';core='hand_grip_keep_core'
    if any(a['role'] in (shell,core) for a in p['atoms']):
        raise ValueError('start from the untrimmed reviewed bow or fitting')
    p['atoms'].extend([
        dict(role=shell,primitive='cube',export=False,dimensions=[1.8,1.8,2*half_length],
             location=center,bevel=0),
        dict(role=core,primitive='cylinder',export=False,radius=radius,depth=2*half_length+.2,
             location=center,vertices=64,bevel=0)])
    p['operations'].append(dict(target=shell,operand=core,operation='DIFFERENCE',solver='EXACT'))
    for target in source.output_roles:
        p['operations'].append(dict(target=target,operand=shell,operation='DIFFERENCE',solver='EXACT'))
    p['grip_profile']=dict(center=center,radius_mm=radius,half_length_mm=half_length,
        outer_trim_width_mm=1.8,parent_reference=source.reference,parent_sha256=source.sha256)
    p['provenance']='Reviewed geometry retained outside the grip; Exact annular subtraction recesses the handle and fitting beneath the fingers. Visual-only.'
    return validate_part(ComponentDefinition.from_dict(data))
