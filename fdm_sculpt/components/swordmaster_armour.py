"""Heavy swordmaster armor and crown braid, built from reusable primitives."""
import math
from .spearmen import sphere,cube,link,part
from .core import ComponentDefinition
from .parts import validate_part
from .elves_v2 import multiply,translation


def cuirass(parent,seed):
    data=parent.to_dict();data.update(component_id='aurelian.swordmaster-cuirass',version=1,name='Swordmaster heavy ridged cuirass')
    p=data['parameters']
    for a in p['atoms']:
        if a['role']=='smooth_chest_plate':a['dimensions']=[2.42,1.98,2.3]
    additions=[]
    for side in (-1,1):
        additions.extend([link(f'collar_{side}',[0,-.76,1.08],[side*.7,-.65,.93],.15),
            link(f'chest_ridge_{side}',[0,-1.16,.12],[side*.7,-.98,.67],.13)])
    p['atoms'].extend(additions)
    p['operations'].extend(dict(target='smooth_chest_plate',operand=a['role'],operation='UNION',solver='EXACT') for a in additions)
    p.update(seed=seed,parent_reference=parent.reference,parent_definition_sha256=parent.sha256)
    return validate_part(ComponentDefinition.from_dict(data))


def pauldrons(seed):
    atoms=[]
    for side in (-1,1):
        tag='left' if side<0 else 'right'
        atoms.append(sphere(tag+'_cap',[side*1.06,0,1.08],[1.5,1.45,.95]))
        for index in range(3):
            a=sphere(f'{tag}_swept_plate_{index}',[side*(1.45+index*.17),.13+index*.27,1.12+index*.16],[1.7,.76,.56])
            angle=-side*math.radians(24);c,s=math.cos(angle),math.sin(angle)
            rotation=[[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
            a['frame_mm']=multiply(translation(a['location']),multiply(rotation,translation([-v for v in a['location']])))
            atoms.append(a)
            atoms.append(link(f'{tag}_raised_rim_{index}',[side*1.04,-.24+index*.27,1.05+index*.15],
                [side*(2.12+index*.13),.10+index*.27,1.57+index*.15],.13))
    return part('swordmaster-swept-pauldrons',atoms,dict(left_shoulder=[-.98,0,.72],right_shoulder=[.98,0,.72]),seed)


def waist_armour(seed):
    atoms=[dict(role='belt',primitive='cylinder',export=True,location=[0,0,-.88],radius=1.22,depth=.66,scale=[1,.8,1],vertices=48,bevel=.07)]
    for side in (-1,1):
        atoms.extend([sphere(f'tasset_{side}',[side*.88,-.77,-1.83],[.98,.65,1.7]),
            link(f'tasset_ridge_{side}',[side*.84,-1.07,-1.15],[side*.98,-1.07,-2.45],.13),
            sphere(f'tasset_stud_{side}',[side*.85,-1.15,-1.38],[.3,.2,.3])])
    atoms.extend([sphere('central_plate',[0,-1.03,-1.73],[1.12,.48,1.65]),
        sphere('belt_jewel',[0,-1.12,-.86],[.65,.35,.62]),
        link('left_scroll',[-.43,-1.27,-1.32],[0,-1.3,-2.3],.115),
        link('right_scroll',[.43,-1.27,-1.32],[0,-1.3,-2.3],.115),
        sphere('lower_jewel',[0,-1.31,-2.13],[.3,.22,.4])])
    d=part('swordmaster-waist-armour',atoms,dict(waist=[0,0,-.88]),seed).to_dict()
    p=d['parameters'];p['atoms'].append(cube('cape_limit',[0,-3.8,-1],[8,8,8],0))
    p['operations'].append(dict(target='belt',operand='cape_limit',operation='INTERSECT',solver='EXACT'))
    return validate_part(ComponentDefinition.from_dict(d))


def crown_braid(seed):
    path=[[0,.08,1.84],[0,.16,2.35],[0,.55,2.69],[0,1.08,2.63],[0,1.6,2.33],[0,2.00,1.9],[0,2.22,1.39],[0,2.27,.88],[0,2.12,.4]]
    atoms=[sphere('crown_binding',path[0],[.73,.73,.56])]
    for i,(a,b) in enumerate(zip(path,path[1:])):
        atoms.append(link(f'braid_core_{i}',a,b,.27 if i<6 else .22))
        for side in (-1,1):
            start=[a[0]+side*.22,a[1],a[2]]
            end=[b[0]-side*.22,b[1],b[2]]
            atoms.append(link(f'plait_{i}_{side}',start,end,.20 if i<6 else .16))
    atoms.append(sphere('tail_binding',path[-1],[.52,.52,.45]))
    for side in (-1,0,1):atoms.append(link(f'tassel_{side}',[side*.12,2.12,.37],[side*.17,1.98,-.14],.13))
    return part('swordmaster-crown-braid',atoms,dict(crown=path[0],tail=path[-1]),seed)


def armour_parts(definitions,seed):
    return [cuirass(definitions['aurelian.chest-plate@4'],seed),pauldrons(seed),waist_armour(seed),crown_braid(seed)]


def rounded_crown_braid(seed):
    data=crown_braid(seed).to_dict();data['version']=2
    data['name']='Swordmaster crown braid with interwoven rounded locks'
    for a in data['parameters']['atoms']:
        if not a['role'].startswith(('plait_','braid_core_','tassel_')):continue
        start,end,r=a['start'],a['end'],a['radius']
        direction=[end[i]-start[i] for i in range(3)];length=math.sqrt(sum(v*v for v in direction))
        z=[v/length for v in direction];x=[1-z[0]*z[0],-z[0]*z[1],-z[0]*z[2]]
        norm=math.sqrt(sum(v*v for v in x));x=[v/norm for v in x]
        y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]]
        center=[(start[i]+end[i])/2 for i in range(3)]
        atom=sphere(a['role'],[0,0,0],[2*r,2*r,length+2*r])
        atom['frame_mm']=[[x[i],y[i],z[i],center[i]] for i in range(3)]+[[0,0,0,1]]
        a.clear();a.update(atom)
    return validate_part(ComponentDefinition.from_dict(data))


def metal_pauldrons(seed):
    atoms=[]
    for side in (-1,1):
        tag='left' if side<0 else 'right'
        center=[side*1.2,0,1.1];a=side*math.radians(18);c,s=math.cos(a),math.sin(a)
        rotation=[[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
        frame=multiply(translation(center),multiply(rotation,translation([-v for v in center])))
        for atom in [cube(tag+'_forged_cap',center,[1.65,1.72,.64],.18),
                     cube(tag+'_raised_panel',[side*1.2,0,1.43],[1.25,1.32,.18],.1)]:
            atom['frame_mm']=frame;atoms.append(atom)
        atoms.append(cube(tag+'_lower_lame',[side*1.62,0,.66],[.66,1.66,.63],.14))
        for y in (-.62,.62):
            atoms.append(sphere(f'{tag}_rivet_{y}',[side*1.72,y,.93],[.2,.2,.2]))
    data=part('swordmaster-swept-pauldrons',atoms,dict(left_shoulder=[-.98,0,.72],right_shoulder=[.98,0,.72]),seed).to_dict()
    data.update(version=2,name='Swordmaster forged metal pauldrons with raised borders')
    return validate_part(ComponentDefinition.from_dict(data))


def helmet_plume(seed):
    path=[[0,.08,1.88],[0,.28,2.26],[0,.62,2.12],[0,.90,1.62],[0,1.08,.99],[0,1.13,.35],[0,1.0,-.28]]
    atoms=[sphere('crown_socket',path[0],[.65,.65,.5])]
    def lock(role,a,b,width,depth,overlap):
        dy,dz=b[1]-a[1],b[2]-a[2];length=math.hypot(dy,dz)
        z=[0,dy/length,dz/length];y=[0,z[2],-z[1]]
        center=[(a[i]+b[i])/2 for i in range(3)]
        atom=sphere(role,[0,0,0],[width,depth,length+overlap])
        atom['frame_mm']=[[1,0,0,center[0]],[0,y[1],z[1],center[1]],[0,y[2],z[2],center[2]],[0,0,0,1]]
        return atom
    for i,(a,b) in enumerate(zip(path,path[1:])):
        width=[.83,1.05,1.06,.97,.85,.62][i]
        atoms.append(lock(f'flowing_plume_{i}',a,b,width,.7,.65))
        for strand in (-2,-1,0,1,2):
            aa=[strand*width*.15,a[1]+.29,a[2]];bb=[strand*width*.14,b[1]+.29,b[2]]
            atoms.append(lock(f'hair_ridge_{i}_{strand}',aa,bb,.14,.17,.38))
    return part('swordmaster-helmet-plume',atoms,dict(crown=path[0],drape=path[-1]),seed)


def flowing_hair_plume(seed):
    """One smooth hair envelope with engraved flowing strands."""
    atoms=[sphere('hair_mass',[0,.95,.95],[1.05,.9,3.0]),
           sphere('crown_sweep',[0,.4,1.95],[.85,1.35,.8]),
           sphere('crown_socket',[0,.1,1.88],[.65,.65,.5])]
    data=part('swordmaster-helmet-plume',atoms,dict(crown=[0,.1,1.88],drape=[0,.95,-.55]),seed).to_dict()
    data.update(version=2,name='Swordmaster flowing hair plume with shallow strand grooves')
    p=data['parameters']
    for strand in (-2,-1,0,1,2):
        points=[]
        for step in range(17):
            z=-.29+step*2.47/16;t=(z-.95)/1.5
            x=(strand*.31+.07*math.sin(t*2+strand*.5))*.525*math.sqrt(1-t*t)
            y=.95+.45*math.sqrt(1-t*t-(x/.525)**2)+.014
            points.append([x,y,z])
        for i,(a,b) in enumerate(zip(points,points[1:])):
            role=f'strand_groove_{strand}_{i}'
            cutter=link(role,a,b,.058);cutter['bevel']=0
            p['atoms'].append(cutter)
            p['operations'].append(dict(target='hair_mass',operand=role,operation='DIFFERENCE',solver='EXACT'))
    p['design']=dict(groove_radius_mm=.058,groove_depth_mm=.044,description='Shallow flowing grooves in one continuous hair mass; no separate raised locks.')
    return validate_part(ComponentDefinition.from_dict(data))


def custom_hair_plume(seed):
    """Asymmetric swept crest and tapered fall, engraved along its surface."""
    center=[.10,1.05,1.0];angle=math.radians(-12);c,s=math.cos(angle),math.sin(angle)
    rotation=[[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
    frame=multiply(translation(center),rotation)
    body=sphere('hair_mass',[0,0,0],[1.15,.78,3.25]);body['frame_mm']=frame
    atoms=[body,sphere('swept_crest',[-.08,.42,2.13],[.82,1.25,.9]),
        sphere('root_flow',[0,.1,1.98],[.54,.63,.62])]
    data=part('swordmaster-helmet-plume',atoms,dict(crown=[0,.1,1.88],drape=[.438,1.05,-.589]),seed).to_dict()
    data.update(version=3,name='Swordmaster custom swept hair plume')
    p=data['parameters']
    def world(v):return [sum(frame[i][j]*v[j] for j in range(3))+frame[i][3] for i in range(3)]
    for strand in range(-3,4):
        points=[]
        for step in range(19):
            # Staggered ends and S-curves keep the hair from reading as comb teeth.
            t=-.89+abs(strand)*.026+step*(1.75-abs(strand)*.044)/18
            fraction=strand*.245+.10*math.sin(2.5*t+strand*.35)
            x=fraction*.575*math.sqrt(1-t*t)
            y=.39*math.sqrt(1-t*t-(x/.575)**2)+.010
            points.append(world([x,y,t*1.625]))
        for i,(a,b) in enumerate(zip(points,points[1:])):
            delta=[(b[j]-a[j])*.10 for j in range(3)]
            role=f'flow_groove_{strand}_{i}'
            cutter=link(role,[a[j]-delta[j] for j in range(3)],[b[j]+delta[j] for j in range(3)],.043)
            cutter['bevel']=0;p['atoms'].append(cutter)
            p['operations'].append(dict(target='hair_mass',operand=role,operation='DIFFERENCE',solver='EXACT'))
    p['design']=dict(groove_depth_mm=.033,side_sweep_degrees=12,
        description='Custom asymmetric hair silhouette with a swept crown, tapered sideways fall and staggered curved strand engraving. Visual-only.')
    return validate_part(ComponentDefinition.from_dict(data))


def fitted_waist_armour(parent):
    """Sink side tassets into the elliptical skirt and follow its flare."""
    data=parent.to_dict();data['version']=2;data['name']+=' with fitted side plates'
    p=data['parameters']
    for side in (-1,1):
        old=[side*.88,-.77,-1.83];new=[side*.78,-.60,-1.83]
        a=math.radians(side*38);c,s=math.cos(a),math.sin(a)
        rz=[[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]]
        a=math.radians(-8);c,s=math.cos(a),math.sin(a)
        rx=[[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]
        frame=multiply(translation(new),multiply(multiply(rz,rx),translation([-v for v in old])))
        roles={f'tasset_{side}',f'tasset_ridge_{side}',f'tasset_stud_{side}',f'layered_plate_{side}'}
        for atom in p['atoms']:
            if atom['role'] not in roles:continue
            for key in ('location','start','end'):
                if key in atom:atom[key][1]=old[1]+(atom[key][1]-old[1])*.65
            if 'dimensions' in atom:atom['dimensions'][1]*=.65
            atom['frame_mm']=frame
    p['side_plate_fit']=dict(turn_degrees=38,flare_degrees=8,depth_scale=.65,center_x_mm=.78,center_y_mm=-.60)
    return validate_part(ComponentDefinition.from_dict(data))


def enlarged_fitted_waist(parent):
    data=fitted_waist_armour(parent).to_dict();data['version']=3
    data['name']+=' enlarged'
    for side in (-1,1):
        center=[side*.88,-.77,-1.83]
        roles={f'tasset_{side}',f'tasset_ridge_{side}',f'tasset_stud_{side}',f'layered_plate_{side}'}
        for a in data['parameters']['atoms']:
            if a['role'] not in roles:continue
            for key in ('location','start','end'):
                if key in a:
                    for axis,scale in ((0,1.25),(2,1.22)):a[key][axis]=center[axis]+(a[key][axis]-center[axis])*scale
            if 'dimensions' in a:
                a['dimensions'][0]*=1.25;a['dimensions'][2]*=1.22
    data['parameters']['side_plate_fit'].update(width_scale=1.25,height_scale=1.22)
    return validate_part(ComponentDefinition.from_dict(data))
