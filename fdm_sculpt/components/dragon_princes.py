"""Original primitive cavalry mount, barding and dragon-prince equipment."""
import math
from .spearmen import sphere,cube,link,part
from .core import ComponentDefinition
from .parts import validate_part

def horse(seed):
    atoms=[sphere('barrel',[0,.3,4.55],[2.5,5.3,2.7]),
        sphere('shoulders',[0,-1.4,4.65],[2.35,2.3,2.9]),sphere('haunches',[0,2,4.55],[2.5,2.1,2.8])]
    neck=sphere('arched_neck',[0,-1.9,6.0],[1.55,2.15,3.6])
    a=math.radians(25);c,s=math.cos(a),math.sin(a)
    neck['frame_mm']=[[1,0,0,0],[0,c,-s,6*s-1.9*(1-c)],[0,s,c,6*(1-c)+1.9*s],[0,0,0,1]]
    atoms.extend([neck,sphere('head',[0,-3.0,7.15],[1.3,2.1,1.35]),sphere('muzzle',[0,-3.95,6.8],[1.1,1.3,.95])])
    for side in (-1,1):
        for rear in (False,True):
            tag=f'{side}_{"hind" if rear else "fore"}'
            hip=[side*.78,1.8 if rear else -1.45,4.4]
            knee=[side*.98,2.35 if rear else -1.75,2.2]
            ankle=[side*1.03,2.55 if rear else -2.13,.7]
            atoms.extend([link(tag+'_upper',hip,knee,.44),sphere(tag+'_knee',knee,[.8,.85,.9]),
                link(tag+'_lower',knee,ankle,.31),cube(tag+'_hoof',[ankle[0],ankle[1]-.16,.35],[.85,1.05,.7],.14)])
        atoms.extend([dict(role=f'ear_{side}',primitive='cone',export=False,location=[side*.46,-2.65,7.91],radius1=.28,radius2=.07,depth=.85,vertices=12,scale=[.7,1,1],bevel=.04),
            sphere(f'eye_{side}',[side*.63,-3.18,7.35],[.23,.32,.24])])
    atoms.extend([sphere('tail_root',[0,2.75,4.55],[.85,1.4,1.35]),sphere('tail_fall',[0,3.12,3.2],[.73,1.0,2.6])])
    return part('dragon-prince-horse',atoms,dict(saddle=[0,.3,5.8],ground=[0,0,0],muzzle=[0,-4.3,6.8]),seed)

def barding(seed):
    atoms=[sphere('chamfron',[0,-3.29,7.48],[1.42,2.1,.55]),cube('noseband',[0,-4.05,6.9],[1.2,.35,1.0],.12)]
    for side in (-1,1):
        atoms.extend([sphere(f'flank_plate_{side}',[side*1.14,.35,4.75],[.54,4.6,2.15]),
            link(f'bridle_{side}',[side*.59,-4.06,6.7],[side*.6,-2.25,7.4],.13)])
        for row in range(2):
            for col in range(6):
                atoms.append(dict(role=f'dragon_scale_{side}_{row}_{col}',primitive='cone',export=False,
                    location=[side*1.44,-1.25+col*.63,5.12-row*.66],radius1=.43,radius2=.35,depth=.2,vertices=4,
                    rotation=[0,side*math.pi/2,0],scale=[1,1.0,1],bevel=.04))
    atoms.append(sphere('chest_barding',[0,-2.20,4.6],[2.0,.55,2.0]))
    for z in (4.1,4.7,5.3):atoms.append(link(f'chest_ridge_{z}',[-.7,-2.48,z],[.7,-2.48,z],.13))
    for i in range(4):atoms.append(dict(role=f'neck_spine_{i}',primitive='cone',export=False,location=[0,-.8-i*.38,6.0+i*.42],radius1=.32,radius2=.07,depth=.62,vertices=4,bevel=.03))
    return part('dragon-prince-barding',atoms,{},seed)

def saddle(seed):
    atoms=[sphere('saddle',[0,.3,5.86],[2.65,2.1,.75]),cube('pommel',[0,-.57,6.13],[1.7,.4,.7],.14),cube('cantle',[0,1.12,6.2],[1.9,.4,.85],.16)]
    return part('dragon-prince-saddle',atoms,dict(seat=[0,.3,6.2]),seed)

def riding_legs(seed):
    atoms=[sphere('hips',[0,.1,6.55],[1.7,1.45,1.3])]
    for side in (-1,1):
        hip=[side*.5,.05,6.6];knee=[side*1.43,-.6,5.2];ankle=[side*1.55,.08,4.07]
        atoms.extend([link(f'thigh_{side}',hip,knee,.48),sphere(f'knee_plate_{side}',knee,[1,.9,.8]),
            link(f'greave_{side}',knee,ankle,.4),cube(f'boot_{side}',[side*1.58,-.18,3.88],[.78,1.28,.65],.13),
            cube(f'stirrup_{side}',[side*1.58,-.16,3.55],[.95,1.05,.22],.07)])
    return part('dragon-prince-riding-legs',atoms,dict(hips=[0,.1,6.55],torso=[0,0,8]),seed)

def rider_arm(side,seed):
    sign=-1 if side=='left' else 1;shoulder=[sign*.98,0,.72]
    elbow=[sign*1.45,-.35,-.1];grip=[sign*1.5,-1,.4]
    atoms=[sphere('shoulder',shoulder,[1.1,1.05,1.1]),link('upper_arm',shoulder,elbow,.44),
        sphere('elbow',elbow,[.9,.9,.9]),link('forearm',elbow,grip,.4),
        cube('fist',grip,[1.0,.95,1.05],.14),sphere('thumb',[grip[0]-.3*sign,-1.38,.65],[.45,.4,.48])]
    return part('dragon-prince-'+side+'-arm',atoms,dict(shoulder=shoulder,grip=grip),seed)

def lance(seed):
    atoms=[dict(role='shaft',primitive='cylinder',export=True,location=[0,0,2.3],radius=.5,depth=8.2,vertices=24,bevel=.03),
        dict(role='point',primitive='cone',export=False,location=[0,0,7.05],radius1=.57,radius2=.10,depth=1.4,vertices=4,bevel=.02),
        dict(role='hand_guard',primitive='cone',export=False,location=[0,0,-.55],radius1=.8,radius2=.51,depth=.48,vertices=24,bevel=.06)]
    return part('dragon-prince-lance',atoms,dict(grip=[0,0,0],tip=[0,0,7.75]),seed)

def dragon_shield(seed):
    atoms=[dict(role='shield',primitive='cone',export=True,location=[0,0,0],radius1=1.1,radius2=1.04,depth=.44,vertices=4,rotation=[math.pi/2,0,0],scale=[1,1.5,1],bevel=.09),
        sphere('dragon_body',[0,-.25,0],[.58,.3,1.1]),link('dragon_neck',[0,-.28,.3],[.28,-.28,.8],.16),
        sphere('dragon_head',[.3,-.3,.83],[.55,.35,.35]),link('dragon_tail',[0,-.28,-.4],[-.4,-.28,-.8],.13)]
    for side in (-1,1):
        atoms.append(link(f'wing_{side}',[0,-.28,.1],[side*.62,-.28,.6],.15))
        atoms.append(link(f'wing_edge_{side}',[side*.62,-.28,.6],[side*.62,-.28,-.1],.12))
    return part('dragon-prince-shield',atoms,dict(grip=[0,.5,0]),seed)

def dragon_helmet(parent,seed):
    data=parent.to_dict();data.update(component_id='aurelian.dragon-prince-helmet',version=1,name='Dragon prince horned steel helmet')
    atoms=[]
    for side in (-1,1):
        atoms.append(dict(role=f'dragon_horn_{side}',primitive='cone',export=False,location=[side*.72,.28,1.5],radius1=.27,radius2=.07,depth=1.25,vertices=8,rotation=[-.28,side*.3,0],bevel=.035))
    p=data['parameters'];p['atoms'].extend(atoms)
    p['operations'].extend(dict(target='helmet_crown',operand=a['role'],operation='UNION',solver='EXACT') for a in atoms)
    p.update(seed=seed,parent_reference=parent.reference)
    return validate_part(ComponentDefinition.from_dict(data))

def cavalry_parts(definitions,seed):return [horse(seed),barding(seed),saddle(seed),riding_legs(seed),rider_arm('left',seed),rider_arm('right',seed),lance(seed),dragon_shield(seed),dragon_helmet(definitions['aurelian.helmet@5'],seed)]


def open_face_barding(seed):
    data=barding(seed).to_dict();data['version']=2
    data['name']='Dragon prince barding with narrow horse face plate'
    plate=next(a for a in data['parameters']['atoms'] if a['role']=='chamfron')
    plate.update(location=[0,-3.55,7.55],dimensions=[.9,1.45,.32])
    return validate_part(ComponentDefinition.from_dict(data))
