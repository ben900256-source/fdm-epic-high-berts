"""Rigid hand-only rotations to match held equipment; sleeves remain pinned."""
from copy import deepcopy

from .elves_v2 import identity, multiply, point, translation
from .robe_arms import hand_atom, unit
from .spearman_overhangs import finish


def direction(matrix, vector):
    return unit([sum(matrix[i][j]*vector[j] for j in range(3)) for i in range(3)])


def align_axis(source, target):
    a,b=unit(source),unit(target)
    # A grip axis is an unoriented line: do not flip a hand upside down.
    if sum(x*y for x,y in zip(a,b))<0:
        b=[-v for v in b]
    v=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    c=sum(x*y for x,y in zip(a,b))
    k=[[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]
    r=identity()
    for i in range(3):
        for j in range(3):
            r[i][j]+=k[i][j]+sum(k[i][s]*k[s][j] for s in range(3))/(1+c)
    return r


def rotation_about(rotation,pivot):
    return multiply(translation(pivot),multiply(rotation,translation([-x for x in pivot])))


def revised_parts(definitions,manifest,seed):
    if type(seed) is not int or seed!=manifest['seed']:
        raise ValueError('seed must match the pinned hand alignment manifest')
    result=[]
    for item in manifest['parts']:
        source=definitions[item['source']]
        if source.sha256!=item['definition_sha256']:
            raise ValueError('pinned source arm changed')
        data=deepcopy(source.to_dict()); p=data['parameters']
        transform=rotation_about(item['rotation'],item['pivot'])
        for atom in p['atoms']:
            if hand_atom(atom):
                atom['frame_mm']=multiply(transform,atom.get('frame_mm',identity()))
        for name,value in p['landmarks'].items():
            if name=='grip_axis':
                p['landmarks'][name]=direction(item['rotation'],value)
            elif hand_atom({'role':name}):
                p['landmarks'][name]=point(transform,value)
        p.update(seed=seed,hand_alignment_source=source.reference,
                 hand_alignment_source_sha256=source.sha256,
                 hand_alignment=dict(rotation=item['rotation'],pivot=item['pivot'],
                                     finger_role=item['finger_role'],target_axis=item['target_axis']),
                 provenance='Rotate palm, grouped fingers, thumb and attached hand details together around the grip to follow the held item. Existing sleeves, elbows and equipment placements retained. Visual-only.')
        data.update(version=item['version'],name=source.name+' with aligned grip')
        result.append(finish(data))
    return result
