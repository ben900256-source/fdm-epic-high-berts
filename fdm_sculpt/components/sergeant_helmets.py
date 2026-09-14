"""Shared winged sergeant helmet built on the approved infantry crown."""
import math

from .core import ComponentDefinition
from .elves_v2 import multiply, translation
from .parts import validate_part


def sergeant_helmet(parent, *, seed):
    if type(seed) is not int:
        raise ValueError('explicit integer seed required')
    if parent.reference != 'aurelian.helmet@5':
        raise ValueError('preserve the approved revision 5 crown')
    data = parent.to_dict()
    data.update(component_id='aurelian.sergeant-helmet', version=1,
                name='Sergeant helmet with swept feather wings')
    p = data['parameters']
    additions = []
    for side in (-1, 1):
        label = 'left' if side < 0 else 'right'
        additions.append(dict(role=label+'_wing_root', primitive='sphere', export=False,
            location=[side*.68,.03,.82], dimensions=[.65,.9,.72], segments=32, ring_count=24))
        for index, (x,y,z,length,angle) in enumerate([
            (.88,-.03,1.30,1.55,18), (1.01,.18,1.35,1.65,26), (1.10,.39,1.28,1.6,34)]):
            center = [side*x,y,z]
            a = math.radians(side*angle)
            c,s = math.cos(a), math.sin(a)
            rotation = [[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
            frame = multiply(translation(center),multiply(rotation,translation([-v for v in center])))
            additions.append(dict(role=f'{label}_wing_feather_{index}',primitive='sphere', export=False,
                location=center, dimensions=[.40,.52,length], frame_mm=frame, segments=32, ring_count=24))
    additions.append(dict(role='brow_jewel', primitive='sphere', export=False,
        location=[0,-.94,.96], dimensions=[.45,.32,.48], segments=32, ring_count=24))
    p['atoms'].extend(additions)
    p['operations'].extend(dict(target='helmet_crown', operand=a['role'], operation='UNION', solver='EXACT') for a in additions)
    p['seed'] = seed
    p['parent'] = dict(reference=parent.reference, definition_sha256=parent.sha256)
    p['landmarks']['wing_roots'] = [[-.68,.03,.82],[.68,.03,.82]]
    p['provenance'] = 'Approved crown, face opening and cap retained; paired swept feather wings and a brow jewel identify sergeants. Visual-only.'
    return validate_part(ComponentDefinition.from_dict(data))


def larger_sergeant_helmet(parent, *, seed):
    data=sergeant_helmet(parent,seed=seed).to_dict()
    data.update(version=2,name='Sergeant helmet with enlarged swept feather wings')
    p=data['parameters']
    for atom in p['atoms']:
        if '_wing_feather_' in atom['role']:
            side=-1 if atom['role'].startswith('left') else 1
            index=int(atom['role'][-1])
            old_length=atom['dimensions'][2]
            axis=[atom['frame_mm'][i][2] for i in range(3)]
            root=[atom['location'][i]-axis[i]*old_length/2 for i in range(3)]
            angle=math.radians(side*[18,26,34][index]*.8)
            c,s=math.cos(angle),math.sin(angle)
            length=old_length*1.5
            center=[root[0]+s*length/2,root[1],root[2]+c*length/2]
            rotation=[[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
            atom.update(location=center,dimensions=[.50,.65,length],
                frame_mm=multiply(translation(center),multiply(rotation,translation([-v for v in center]))))
        elif atom['role'].endswith('_wing_root'):
            atom['dimensions']=[v*1.1 for v in atom['dimensions']]
    p['ornament_scale']=dict(feather_length=1.5,feather_width=1.25,wing_root=1.1)
    p['provenance']='Revision 1 crown and jewel retained; feathers lengthened 50 percent from their existing roots and broadened 25 percent, swept more upright. Visual-only.'
    return validate_part(ComponentDefinition.from_dict(data))
