"""Ten two-handed swordmaster guards with fixed shoulder attachments."""
import math
from .swordmasters import guard_arm,UPPER_GRIP,LOWER_GRIP
from .elves_v2 import multiply,translation
from .core import ComponentDefinition
from .parts import validate_part

POSES=[
    ('diagonal-guard',30,0,[.35,-1.7,.55],0),
    ('high-guard',15,15,[.55,-1.75,1.1],-3),
    ('left-guard',-30,12,[-.35,-1.8,.65],3),
    ('wide-parry',55,20,[.55,-1.9,.35],-4),
    ('left-parry',-50,20,[-.5,-1.9,.35],4),
    ('forward-point',20,60,[.3,-1.8,.15],0),
    ('high-right',40,8,[.45,-1.8,1.0],-3),
    ('low-guard',65,25,[.45,-1.95,-.25],3),
    ('recovering',-15,35,[-.2,-2,.85],-4),
    ('upright-guard',0,10,[.6,-1.95,.7],4),
]

def rotation(axis,degrees):
    a=math.radians(degrees);c,s=math.cos(a),math.sin(a)
    if axis=='x':return [[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]
    if axis=='y':return [[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
    return [[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]]

def sword_rotation(pose):return multiply(rotation('x',pose[2]),rotation('y',pose[1]))

def posed_arm(number,side,seed):
    if number==1:return guard_arm(side,seed)
    pose=POSES[number-1];r=sword_rotation(pose);upper=pose[3]
    grip=upper if side=='right' else [upper[i]-1.15*r[i][2] for i in range(3)]
    old=UPPER_GRIP if side=='right' else LOWER_GRIP
    elbow=[1.5,-.75,-.15] if side=='right' else [-1.3,-.75,-.35]
    elbow[2]+=(upper[2]-.55)*.55
    data=guard_arm(side,seed).to_dict()
    data.update(component_id=f'aurelian.swordmaster-{side}-arm-pose-{number:02d}',name=f'Swordmaster {side} arm: {pose[0]}')
    p=data['parameters']
    for a in p['atoms']:
        role=a['role']
        if role=='upper_arm':a['end']=elbow
        elif role=='elbow':a['location']=elbow
        elif role=='forearm':a.update(start=elbow,end=grip)
        elif role in ('palm','fingers','thumb'):
            a['location']=[a['location'][i]+grip[i]-old[i] for i in range(3)]
            a['frame_mm']=multiply(translation(grip),multiply(r,translation([-v for v in grip])))
    p['landmarks'].update(elbow=elbow,grip=grip)
    p['pose']=pose[0]
    return validate_part(ComponentDefinition.from_dict(data))
