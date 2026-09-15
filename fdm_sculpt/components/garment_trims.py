"""Overlapping garment edging with a recessed front and hem crease."""
import math
from copy import deepcopy
from .core import ComponentDefinition
from .parts import validate_part


def garment_trim(kind, *, seed, revision=1):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    if revision not in (1,2,3,4):raise ValueError('unsupported trim revision')
    if revision>=3 and kind!='mail-skirt':raise ValueError('later revisions are the waist-wrap mail trim')
    if kind=='tunic':
        bottom,top,r_bottom,r_top,scale=-3.5,-.5,1.77,.92,.72
    elif kind=='mail-skirt':
        bottom,top,r_bottom,r_top,scale=-4.85,-.5,1.55,.97,.75
    else:
        raise ValueError('unknown garment')
    def radius(z):return r_bottom+(r_top-r_bottom)*(z-bottom)/(top-bottom)
    def cone(role,z0,z1,extra):
        return dict(role=role,primitive='cone',export=False,location=[0,0,(z0+z1)/2],
            radius1=radius(z0)+extra,radius2=radius(z1)+extra,depth=z1-z0,
            scale=[1,scale,1],vertices=64,bevel=0)
    height=.50; groove_z=bottom+.25
    atoms=[cone('hem_trim',bottom,bottom+height,.36 if revision==1 else .44),cone('hem_inner',bottom-.1,bottom+height+.1,-.09)]
    atoms[0]['export']=True
    operations=[dict(target='hem_trim',operand='hem_inner',operation='DIFFERENCE',solver='EXACT')]
    z0,z1=groove_z,top-.16
    y0,y1=-radius(z0)*scale-.04,-radius(z1)*scale-.04
    angle=-math.atan2(y1-y0,z1-z0)
    atoms.append(dict(role='front_trim',primitive='cube',export=False,location=[0,(y0+y1)/2,(z0+z1)/2],
        dimensions=[.68,.5 if revision==1 else .62,math.hypot(y1-y0,z1-z0)+.18],rotation=[angle,0,0],bevel=.06))
    operations.append(dict(target='hem_trim',operand='front_trim',operation='UNION',solver='EXACT'))
    atoms.extend([cone('hem_crease_outer',groove_z-.075,groove_z+.075,.65),
                  cone('hem_crease_inner',groove_z-.12,groove_z+.12,.22 if revision==1 else .32)])
    operations.extend([dict(target='hem_crease_outer',operand='hem_crease_inner',operation='DIFFERENCE',solver='EXACT'),
                       dict(target='hem_trim',operand='hem_crease_outer',operation='DIFFERENCE',solver='EXACT')])
    crease_offset=.24 if revision==1 else .30
    atoms.append(dict(role='front_crease',primitive='between',export=False,
        start=[0,y0-crease_offset,z0],end=[0,y1-crease_offset,z1+.04],radius=.105,bevel=0))
    operations.append(dict(target='hem_trim',operand='front_crease',operation='DIFFERENCE',solver='EXACT'))
    if revision>=3:
        atoms.append(dict(role='waist_wrap_limit',primitive='cube',export=False,
            location=[0,0,-5.25],dimensions=[8,8,8],bevel=0))
        operations.append(dict(target='hem_trim',operand='waist_wrap_limit',operation='INTERSECT',solver='EXACT'))
    if revision==4:
        atoms.append(dict(role='cape_clearance_limit',primitive='cube',export=False,
            location=[0,-4.5,-3],dimensions=[8,8,8],bevel=0))
        operations.append(dict(target='hem_trim',operand='cape_clearance_limit',operation='INTERSECT',solver='EXACT'))
    return validate_part(ComponentDefinition.from_dict(dict(component_id='aurelian.'+kind+'-trim',version=revision,
        name=kind.replace('-',' ').title()+' front and hem trim',family='garment-trim',
        required_anchors=['mount'],semantic_slots=['mono'],output_roles=['hem_trim'],
        parameters=dict(atoms=atoms,operations=operations,landmarks=dict(mount=[0,0,0],hem=[0,0,bottom]),
            seed=seed,garment=kind,design=dict(front_band_width_mm=.68,hem_band_height_mm=.5,
                hem_crease_height_mm=.15,front_crease_width_mm=.21),
            provenance='Original primitive and ordered Exact garment edging; overlaps the approved garment without changing its geometry. Visual-only.'))))


def cape_fitted_mail_trim(cape, *, seed, revision=6):
    """Continue the hem to the actual cape surface, using its pinned primitives."""
    data=garment_trim('mail-skirt',seed=seed,revision=3).to_dict()
    suffix=cape.component_id.removeprefix('aurelian.cape')
    data['component_id']='aurelian.mail-skirt-trim'+suffix
    if revision not in (5,6,7):raise ValueError('unsupported cape contact revision')
    data['version']=revision
    params=data['parameters']
    source=cape.to_dict()['parameters']
    roles={a['role']:'cape_contact_'+a['role'] for a in source['atoms']}
    for atom in source['atoms']:
        copy=deepcopy(atom);copy['role']=roles[atom['role']];copy['export']=False
        if revision>=7:
            # Move the cutout rearward, leaving attached relief inside the cape.
            frame=copy.get('frame_mm',[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
            frame[1][3]+=.04
            copy['frame_mm']=frame
        params['atoms'].append(copy)
    for operation in source['operations']:
        copy=deepcopy(operation)
        for key in ('target','operand'):copy[key]=roles[copy[key]]
        params['operations'].append(copy)
    for role in cape.to_dict()['output_roles']:
        params['operations'].append(dict(target='hem_trim',operand=roles[role],operation='DIFFERENCE',solver='EXACT'))
    if revision>=6:
        params['atoms'].append(dict(role='cape_rear_limit',primitive='cube',export=False,
            location=[0,-3.5,-3],dimensions=[8,8,8],bevel=0))
        params['operations'].append(dict(target='hem_trim',operand='cape_rear_limit',operation='INTERSECT',solver='EXACT'))
    params['cape_reference']=cape.reference
    params['cape_definition_sha256']=cape.sha256
    if revision>=7:
        params['cape_contact_overlap_mm']=.04
    return validate_part(ComponentDefinition.from_dict(data))
