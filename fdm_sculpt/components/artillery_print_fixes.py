"""Primitive artillery revisions for a print trial without removable supports."""
from copy import deepcopy
import math
import json
from pathlib import Path
from .core import ComponentDefinition
from .parts import validate_part
from .army_expansion import PREFIX, bolt_thrower, crew_arms_v2, definition, taper
from .chariot_print_fixes import driver_coat_v3, helmet
from .refined_horse import _frame, _chain
from .spearmen import cube, link
from .elves_v2 import multiply, rotation, translation


def finish(data, name, version, notes):
    data.update(component_id=PREFIX+name, version=version, name=name.replace('-', ' ').capitalize(), family='army-expansion-'+name)
    p=data['parameters'];p['design_notes']=notes
    p['audit_source']='docs/bolt-thrower-support-trial.md'
    data['output_roles']=[a['role'] for a in p['atoms'] if a['export']]
    return validate_part(ComponentDefinition.from_dict(data))


def web(role, a, b, bottom_z, thickness):
    # Native triangular cylinder: apex +Y, base at Y=-0.5. Place the apex
    # beneath the midpoint of a horizontal top edge. No manual mesh vertices.
    assert abs(a[2]-b[2])<1e-8
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);u=[dx/length,dy/length,0]
    h=a[2]-bottom_z;center=[(a[0]+b[0])/2,(a[1]+b[1])/2,a[2]-h/3]
    down=[0,0,-1];normal=[-u[1],u[0],0]
    frame=[[u[i],down[i],normal[i],center[i]] for i in range(3)]+[[0,0,0,1]]
    return dict(role=role,primitive='cone',export=True,location=[0,0,0],radius1=1,radius2=1,
                depth=thickness,vertices=3,bevel=0,scale=[length/math.sqrt(3),2*h/3,1],frame_mm=frame)


def clip_above(data, target, role, anchor, normal):
    size=20;length=math.sqrt(sum(v*v for v in normal));normal=[v/length for v in normal]
    center=[anchor[i]+normal[i]*size/2 for i in range(3)]
    frame=_frame(center,[center[i]+normal[i] for i in range(3)])
    # _frame positions its origin at the segment midpoint; restore plane center.
    for i in range(3):frame[i][3]=center[i]
    data['parameters']['atoms'].append(dict(cube(role,[0,0,0],[40,40,size],0),frame_mm=frame,export=False))
    data['parameters']['operations'].append(dict(target=target,operand=role,operation='INTERSECT',solver='EXACT'))


def engine(seed):
    data=bolt_thrower(seed).to_dict();p=data['parameters']
    # A keel grows from the base under the full stock and loaded points. It
    # widens gradually across X, leaving the separate bolts raised on top.
    keel=web('tapered_stock_keel',[0,-4.30,4.45],[0,2.85,4.45],-.10,2.36)
    p['atoms'].append(keel)
    for side in (-1,1):
        clip_above(data,keel['role'],f'keel_side_{side}',[side*.39,0,-.10],[-side,0,.79/4.55])
        bow=web(f'bow_brace_{side}',[0,-1.8,4.18],[side*3.65,-.98,4.18],-.08,.78)
        string=web(f'string_brace_{side}',[0,2.06,4.42],[side*3.62,-.99,4.42],-.08,.78)
        p['atoms'] += [bow,string]
        # Broad feet avoid printing a mathematical triangle apex in midair.
        for tag,a,b in [('bow',[0,-1.8],[side*3.65,-.98]),('string',[0,2.06],[side*3.62,-.99])]:
            xy=[(a[i]+b[i])/2 for i in range(2)]
            p['atoms'].append(dict(cube(f'{tag}_brace_foot_{side}',[*xy,.13],[1.02,1.02,.46],.09),export=True))
        p['atoms'].append(dict(link(f'bow_end_saddle_{side}',[side*3.5,-1.01,3.94],[side*3.65,-.98,4.56],.38),export=True))
        p['atoms'].append(dict(link(f'crank_underside_{side}',[side*.45,2.25,2.75],[side*1.23,2.55,4.0],.34),export=True))
    # The existing screw was suspended above ground between the rear legs.
    screw=next(a for a in p['atoms'] if a['role']=='elevation_screw');screw['start'][2]=-.08
    p['minimum_web_mm']=.78;p['keel_bottom_width_mm']=.78;p['grounded_screw_bottom_mm']=-.08
    return finish(data,'bolt-thrower',2,'Permanent tapered stock keel and thin triangular bow/string braces grow from broad base contacts. Original bow, bolt rack, three loaded bolts and four leg endpoints retained; trial requires sliced checks.')


def crew_arms(seed):
    data=crew_arms_v2(seed).to_dict();p=data['parameters']
    for a in p['atoms']:
        if a['role'].startswith('palm_'):
            a.update(primitive='sphere',segments=40,ring_count=24);a.pop('bevel',None)
    for side in (-1,1):
        grip=p['landmarks']['right_grip' if side==1 else 'left_grip']
        chain=_chain(f'sleeve_return_{side}',[([side*.57,-.22,-3.45],.41),(grip,.52)])
        for a in chain:
            a['export']=False;p['atoms'].append(a)
            p['operations'].append(dict(target=f'palm_{side}',operand=a['role'],operation='UNION',solver='EXACT'))
    p['sleeve_root_z_mm']=-3.45
    return finish(data,'crew-arms',3,'Rounded hands and steep lower sleeve folds meet the legs beneath the wrists. Original shoulder, elbow, grip and finger landmarks retained.')


def crew_coat(seed):
    return finish(driver_coat_v3(seed).to_dict(),'artillery-crew-coat',1,'Artillery-local copy of the hip-supported coat: shortened split tails and paired tapered lower panels. Shared cavalry and chariot references unchanged.')


def crew_helmet(seed):
    return finish(helmet(seed).to_dict(),'artillery-helmet',1,'Artillery-local sloping face-window ceiling. Approved outer pointed helmet and the shared head/nose remain unchanged.')


def grounded_bolt(seed):
    grip=[1.45,-1.30,-1.45];axis=[.28,-.06,math.sqrt(1-.28**2-.06**2)]
    def at(z):return [grip[i]+axis[i]*(z-grip[2])/axis[2] for i in range(3)]
    bottom,neck,tip=at(-5.30),at(.50),at(1.50)
    shaft=dict(link('spare_bolt',bottom,neck,.50),export=True)
    head=dict(taper('spare_bolt_tip',at(.42),tip,.61,.16,vertices=4),export=True)
    d=definition('loader-bolt',[shaft,head],seed,landmarks=dict(grip=grip,shaft_bottom=bottom,tip=tip),
                 notes='Spare bolt stands at 16.6 degrees from vertical through the unchanged right grip; butt intersects the base. The loader left hand remains at the engine.').to_dict()
    d['parameters']['shaft_diameter_mm']=1.0
    return finish(d,'loader-bolt',2,d['parameters']['design_notes'])


def engine_v3(seed):
    data=engine(seed).to_dict();p=data['parameters']
    i=next(i for i,a in enumerate(p['atoms']) if a['role']=='tapered_stock_keel')
    p['atoms'][i]=web('tapered_stock_keel',[0,-4.30,4.62],[0,2.85,4.62],-.10,2.36)
    rear=taper('rear_stock_buttress',[0,1.7,-.08],[0,2.32,3.55],.36,.90,vertices=4)
    rear['frame_mm']=multiply(rear['frame_mm'],rotation([0,0,45]));rear['export']=True;p['atoms'].append(rear)
    # Pointed arch openings keep the braces readable as a frame. The closing
    # sides rise at about 68 degrees; the short roof apex is covered by stock.
    for side in (-1,1):
        for tag in ('bow','string'):
            target=f'{tag}_brace_{side}';brace=next(a for a in p['atoms'] if a['role']==target)
            frame=deepcopy(brace['frame_mm']);frame[2][3]=2.65
            # Flip local X and Y, retaining a right-handed frame: apex points up.
            for row in frame[:3]:row[0]*=-1;row[1]*=-1
            width=.70 if tag=='bow' else 1.10;height=1.25
            hole=dict(role=target+'_arch',primitive='cone',export=False,location=[0,0,0],radius1=1,radius2=1,
                depth=2,vertices=3,bevel=0,scale=[width/math.sqrt(3),2*height/3,1],frame_mm=frame)
            p['atoms'].append(hole);p['operations'].append(dict(target=target,operand=hole['role'],operation='DIFFERENCE',solver='EXACT'))
    return finish(data,'bolt-thrower',3,'Raised supporting bed reaches the bolt points; a rear buttress backs the breech and stock end. Pointed openings lighten the permanent bow and string braces without flat ceilings.')


def crew_arms_v4(seed):
    data=crew_arms(seed).to_dict();p=data['parameters']
    p['atoms']=[a for a in p['atoms'] if not a['role'].startswith('sleeve_return_')]
    p['operations']=[o for o in p['operations'] if not o['operand'].startswith('sleeve_return_')]
    for side,name in ((-1,'left'),(1,'right')):
        source=json.loads((Path(__file__).parent/'parts'/f'aurelian.{name}-leg-c@6.json').read_text())
        root=source['parameters']['landmarks'][name+'_ankle'];grip=p['landmarks']['right_grip' if side==1 else 'left_grip']
        for a in _chain(f'sleeve_return_{side}',[(root,.36),(grip,.52)]):
            a['export']=False;p['atoms'].append(a);p['operations'].append(dict(target=f'palm_{side}',operand=a['role'],operation='UNION',solver='EXACT'))
    p.pop('sleeve_root_z_mm',None)
    return finish(data,'crew-arms',4,'Lower sleeve folds start inside the actual planted ankle axes, then rise steeply to the original wrists. Rounded palms, hands and upper arm poses retained.')


def boot_seats(seed):
    from .elves_v2 import point
    atoms=[]
    for side in ('left','right'):
        source=json.loads((Path(__file__).parent/'parts'/f'aurelian.{side}-leg-c@6.json').read_text())
        sole=next(a for a in source['parameters']['atoms'] if a['role']==side+'_sole')
        at=point(sole['frame_mm'],sole['location']);at[2]=-5.30
        angle=math.degrees(math.atan2(sole['frame_mm'][1][0],sole['frame_mm'][0][0]))
        atoms.append(dict(cube(side+'_boot_seat',[0,0,0],[sole['dimensions'][0]+.035,sole['dimensions'][1]+.035,.66],.05),frame_mm=multiply(translation(at),rotation([0,0,angle]))))
    return definition('artillery-boot-seats',atoms,seed,notes='Thin level soles extend the posed shoe outlines into the artillery base, filling the tilted underside contacts.')


def crew_leg(side, seed):
    source=json.loads((Path(__file__).parent/'parts'/f'aurelian.{side}-leg-c@6.json').read_text())
    p=source['parameters'];p.update(seed=seed,visual_only=True,export_scale=1.3)
    points=p['landmarks']
    nodes=[(points[side+'_boot_instep'],.40),(points[side+'_ankle'],.45),(points[side+'_knee'],.53),(points[side+'_hip'],.55)]
    target=side+'_shin'
    for a in _chain(side+'_leg_blend',nodes):
        if a['primitive']=='cone':a['radius1']+=.015;a['radius2']+=.015
        a['export']=False;p['atoms'].append(a);p['operations'].append(dict(target=target,operand=a['role'],operation='UNION',solver='EXACT'))
    return finish(source,'artillery-'+side+'-leg',1,'Round tangent blends grow from the planted shoe through the unchanged ankle, knee and hip landmarks. Slightly fuller calf and knee undersides remove the original spherical joint ledge.')


def all_parts(seed):
    return [engine(seed),crew_arms(seed),crew_coat(seed),crew_helmet(seed),grounded_bolt(seed),engine_v3(seed),crew_arms_v4(seed),boot_seats(seed),crew_leg('left',seed),crew_leg('right',seed)]
