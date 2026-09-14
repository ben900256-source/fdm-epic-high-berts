"""Raised shooting poses with fixed shoulders and aligned equipment."""
from copy import deepcopy
import math
from .core import ComponentDefinition
from .parts import validate_part


def elevation_transform(degrees, pivot):
    a=math.radians(-degrees);c,s=math.cos(a),math.sin(a)
    m=[[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]
    for i in range(3):m[i][3]=pivot[i]-sum(m[i][j]*pivot[j] for j in range(3))
    return m


def point(matrix, value):
    return [sum(matrix[i][j]*value[j] for j in range(3))+matrix[i][3] for i in range(3)]


def elevated_arm(parent, *, degrees, seed):
    if type(seed) is not int:raise ValueError('explicit integer seed required')
    if degrees not in (20,30,40):raise ValueError('unsupported elevation')
    data=deepcopy(parent.to_dict())
    data['component_id']+=f'-elevated-{degrees}'
    data['version']=1
    data['name']+=f' aiming upward {degrees} degrees'
    params=data['parameters'];m=elevation_transform(degrees,[.55,-.75,1.8])
    for atom in params['atoms']:
        if atom['role'].endswith('_shoulder'):continue
        if atom['role'].endswith('_upper_arm'):
            atom['end']=point(m,atom['end'])
        else:atom['frame_mm']=m
    for key in ('elbow','grip'):params['landmarks'][key]=point(m,params['landmarks'][key])
    params.update(seed=seed,elevation_degrees=degrees,parent_reference=parent.reference,parent_definition_sha256=parent.sha256)
    return validate_part(ComponentDefinition.from_dict(data))
