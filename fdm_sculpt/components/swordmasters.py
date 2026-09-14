"""Original two-handed greatsword and paired guard-pose arms."""
import math
from .spearmen import sphere,cube,link,part
from .elves_v2 import multiply,translation

ANGLE=math.radians(30)
ROTATION=[[math.cos(ANGLE),0,math.sin(ANGLE),0],[0,1,0,0],[-math.sin(ANGLE),0,math.cos(ANGLE),0],[0,0,0,1]]
UPPER_GRIP=[.35,-1.7,.55]
LOWER_GRIP=[UPPER_GRIP[i]-1.15*ROTATION[i][2] for i in range(3)]


def greatsword(seed):
    atoms=[dict(role='grip',primitive='cylinder',export=True,location=[0,0,-.55],radius=.38,depth=2.4,vertices=32,bevel=.04),
        sphere('pommel',[0,0,-1.9],[.95,.8,.65]),
        cube('guard',[0,0,.75],[2.1,.65,.34],.08),
        link('guard_left',[-.95,0,.75],[-1.2,0,1.0],.18),
        link('guard_right',[.95,0,.75],[1.2,0,1.0],.18),
        dict(role='blade',primitive='cone',export=False,location=[0,0,2.92],radius1=.68,radius2=.53,depth=4.2,vertices=4,scale=[1,.48,1],bevel=.025),
        dict(role='point',primitive='cone',export=False,location=[0,0,5.75],radius1=.54,radius2=.10,depth=1.5,vertices=4,scale=[1,.48,1],bevel=.015),
        sphere('guard_gem',[0,-.34,.78],[.46,.26,.42])]
    for i in range(6):
        atoms.append(dict(role=f'hilt_wrap_{i}',primitive='cylinder',export=False,location=[0,0,-1.55+i*.38],radius=.41,depth=.1,vertices=24,bevel=.025))
    return part('swordmaster-greatsword',atoms,dict(upper_grip=[0,0,0],lower_grip=[0,0,-1.15],guard=[0,0,.75],tip=[0,0,6.5]),seed)


def guard_arm(side,seed):
    left=side=='left';sign=-1 if left else 1
    shoulder=[sign*.98,0,.72]
    elbow=[-1.3,-.65,-.35] if left else [1.5,-.7,-.15]
    grip=LOWER_GRIP if left else UPPER_GRIP
    atoms=[sphere('shoulder',shoulder,[1.15,1.1,1.15]),link('upper_arm',shoulder,elbow,.45),
        sphere('elbow',elbow,[.9,.9,.9]),link('forearm',elbow,grip,.43)]
    frame=multiply(translation(grip),multiply(ROTATION,translation([-v for v in grip])))
    for atom in [cube('palm',grip,[1.02,.98,.98],.13),
                 cube('fingers',[grip[0],grip[1]-.38,grip[2]],[.96,.34,.8],.09),
                 sphere('thumb',[grip[0]-sign*.4,grip[1]-.24,grip[2]+.32],[.48,.5,.48])]:
        atom['frame_mm']=frame;atoms.append(atom)
    atoms.append(sphere('pauldron',[shoulder[0],-.04,.94],[1.35,1.25,.8]))
    atoms.append(link('pauldron_rim',[shoulder[0]-.48,-.5,.77],[shoulder[0]+.48,-.5,.77],.14))
    return part('swordmaster-'+side+'-arm',atoms,dict(shoulder=shoulder,elbow=elbow,grip=grip),seed)


def swordmaster_parts(seed):return [greatsword(seed),guard_arm('left',seed),guard_arm('right',seed)]
