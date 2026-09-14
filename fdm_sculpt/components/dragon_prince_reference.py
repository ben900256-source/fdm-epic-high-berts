"""Primitive interpretation of the official Old World cavalry reference.

Reference: https://assets.warhammer-community.com/preorders-apr19-tow_03-dragonprinces-hiahpptwh9.jpg
Broad metal membranes, swept ribs and draped barding are emphasized at 8 mm scale.
"""
import math
from .core import ComponentDefinition
from .parts import validate_part
from .spearmen import sphere, cube, link, part
from .dragon_princes import horse, lance
from .dragon_princes import dragon_shield


def supported_lance_seal(seed):
    data=lance(seed).to_dict();p=data['parameters']
    # Shaft-backed tab replaces the 0.35 mm horizontal free ribbon.
    extra=[cube('supported_seal_tab',[0,.30,5.40],[1.0,.85,1.30],.045),
           dict(role='seal_lower_ramp',primitive='cone',export=False,
                location=[0,.24,4.56],radius1=.24,radius2=.65,depth=.70,
                vertices=4,scale=[.77,.65,1],bevel=.025),
           sphere('seal_boss',[0,.64,5.76],[1.02,.65,.80])]
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='shaft',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    p['design_notes']='FDM-oriented shaft-backed seal; 1.0 x 0.85 mm tab, tapered lower join. Pending sliced and physical validation.'
    return revision(ComponentDefinition.from_dict(data),3,'Dragon Prince lance with supported thick seal tab')


def tapestry_lance(seed):
    data=lance(seed).to_dict();p=data['parameters']
    extra=[]
    for i,(y,z) in enumerate(((.33,5.48),(.41,4.78),(.33,4.08))):
        extra.append(cube(f'tapestry_fold_{i}',[0,y,z],[1.22,.86,1.02],.055))
    extra.extend([
        dict(role='tapestry_lower_join',primitive='cone',export=False,
             location=[0,.22,3.53],radius1=.23,radius2=.68,depth=.68,vertices=4,
             scale=[.91,.69,1],bevel=.03),
        sphere('tapestry_seal',[0,.65,5.86],[1.08,.67,.84]),
        cube('woven_hem',[0,.75,3.86],[1.1,.28,.22],.04)])
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='shaft',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    p['design_notes']='Downward folded tapestry, continuously shaft-backed with tapered lower join. Pending sliced/physical validation.'
    return revision(ComponentDefinition.from_dict(data),4,'Dragon Prince lance with hanging attached tapestry seal')


REIN_ROUTE = ((-.6,-4,7.25),(-1.12,-3.7,6.85),(-1.18,-2.75,6.3),
              (-1.0,-1.35,6.5),(-.9,-1.25,7.7),(-1.5,-1,8.4))


def routed_reins(seed):
    atoms=[link(f'rein_segment_{i}',a,b,.12) for i,(a,b) in enumerate(zip(REIN_ROUTE,REIN_ROUTE[1:]))]
    atoms.extend(sphere(f'rein_bend_{i}',p,[.24,.24,.24]) for i,p in enumerate(REIN_ROUTE[1:-1]))
    return revision(part('dragon-prince-reins',atoms,dict(bit=list(REIN_ROUTE[0]),grip=list(REIN_ROUTE[-1])),seed),
                    3,'Dragon Prince reins routed below cheek armor and behind shield')


def flush_reins(seed):
    # Project the cheek/neck route onto the horse's original ellipsoid surfaces.
    # This stays Blender-free and preserves the reviewed horse geometry.
    surfaces=[a for a in flexed_steed(seed).to_dict()['parameters']['atoms']
              if a['role'] in ('head','muzzle','arched_neck','upper_neck','shoulders','barrel')]
    path=[]
    surface_route=((-.6,-4,7.25),(0,-3.7,7.20),(0,-2.75,6.8),(0,-1.35,6.5),(0,-1.25,7.7))
    for a,b in zip(surface_route,surface_route[1:]):
        for step in range(8):
            t=step/8;y=a[1]*(1-t)+b[1]*t;z=a[2]*(1-t)+b[2]*t
            edges=[]
            for surface in surfaces:
                frame=surface.get('frame_mm',[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
                # Inverse rigid rotation; these anatomical frames rotate about X.
                local_y=frame[1][1]*(y-frame[1][3])+frame[2][1]*(z-frame[2][3])
                local_z=frame[1][2]*(y-frame[1][3])+frame[2][2]*(z-frame[2][3])
                rx,ry,rz=[v/2 for v in surface['dimensions']]
                cx,cy,cz=surface['location']
                q=1-((local_y-cy)/ry)**2-((local_z-cz)/rz)**2
                if q>=0:edges.append(cx-rx*math.sqrt(q))
            if not edges:raise ValueError(f'rein route leaves cheek/neck surface: {y}, {z}')
            path.append([min(edges)-.045,y,z])
    path.extend([[-.72,-1.25,7.7],list(REIN_ROUTE[-1])])
    atoms=[link(f'rein_segment_{i}',a,b,.12) for i,(a,b) in enumerate(zip(path,path[1:]))]
    atoms.extend(sphere(f'rein_bend_{i}',p,[.24,.24,.24]) for i,p in enumerate(path[1:-1]))
    data=part('dragon-prince-reins',atoms,dict(bit=list(REIN_ROUTE[0]),grip=list(REIN_ROUTE[-1])),seed).to_dict()
    data['parameters']['surface_contact_segments']=list(range(31))
    data['parameters']['design_notes']='Shallow deliberate cheek/neck overlap; final short return reaches the unchanged hand.'
    return revision(ComponentDefinition.from_dict(data),4,'Dragon Prince reins flush along cheek and neck')


def angular_pauldrons(seed):
    data=winged_pauldrons(seed).to_dict();p=data['parameters']
    for i,a in enumerate(p['atoms']):
        if a['role'].startswith('shoulder_shell_'):
            side=-1 if a['location'][0]<0 else 1
            cap=cube(a['role'],[side*1.04,.02,.88],[1.26,1.50,.64],.045)
            cap['rotation']=[.12,side*.32,0]
            cap['export']=a['export']
            p['atoms'][i]=cap
    return revision(ComponentDefinition.from_dict(data),2,'Dragon Prince sharply angled metal pauldrons')


def fitted_reins(seed):
    data=flush_reins(seed).to_dict();p=data['parameters']
    segments=[a for a in p['atoms'] if a['primitive']=='between']
    path=[a['start'][:] for a in segments]+[segments[-1]['end'][:]]
    # Shallow relief follows the bridle and neck lame where they cover the skin.
    offsets={0:.08,1:.12,2:.12,3:.12,4:.10,5:.04,19:.04,20:.08,21:.10,22:.04}
    for i,offset in offsets.items():path[i][0]-=offset
    p['atoms']=[link(f'rein_segment_{i}',a,b,.12) for i,(a,b) in enumerate(zip(path,path[1:]))]
    p['atoms'].extend(sphere(f'rein_bend_{i}',v,[.24,.24,.24]) for i,v in enumerate(path[1:-1]))
    p['atoms'][0]['export']=True
    p['surface_contact_segments']=list(range(32))
    return revision(ComponentDefinition.from_dict(data),5,'Dragon Prince reins fitted flush over cheek and armor')


def bridle_fitted_reins(seed):
    data=fitted_reins(seed).to_dict();p=data['parameters']
    segments=[a for a in p['atoms'] if a['primitive']=='between']
    path=[a['start'][:] for a in segments]+[segments[-1]['end'][:]]
    for i in range(7):path[i][0]=-.77
    path[7][0]=-.66;path[8][0]=-.55;path[9][0]=-.50
    p['atoms']=[link(f'rein_segment_{i}',a,b,.12) for i,(a,b) in enumerate(zip(path,path[1:]))]
    p['atoms'].extend(sphere(f'rein_bend_{i}',v,[.24,.24,.24]) for i,v in enumerate(path[1:-1]))
    p['atoms'][0]['export']=True
    return revision(ComponentDefinition.from_dict(data),6,'Dragon Prince flush reins over bridle and cheek')


def larger_shield(seed):
    data=dragon_shield(seed).to_dict()
    # Enlarge the plate and emblem together; keep thickness and rear grip fixed.
    for atom in data['parameters']['atoms']:
        for key in ('location','start','end','dimensions'):
            if key in atom:
                atom[key][0]*=1.35;atom[key][2]*=1.30
        if atom['role']=='shield':atom['scale']=[1.35,1.95,1]
    return revision(ComponentDefinition.from_dict(data),2,'Dragon Prince enlarged shield')


def great_shield(seed):
    data=larger_shield(seed).to_dict()
    for atom in data['parameters']['atoms']:
        for key in ('location','start','end','dimensions'):
            if key in atom:
                atom[key][0]*=1.25;atom[key][2]*=1.25
        if atom['role']=='shield':
            atom['scale'][0]*=1.25;atom['scale'][1]*=1.25
    return revision(ComponentDefinition.from_dict(data),3,'Dragon Prince great shield')


def gem_shield(seed):
    plate=great_shield(seed).to_dict()['parameters']['atoms'][0]
    atoms=[plate,sphere('oval_gem_setting',[0,-.28,0],[1.02,.38,1.65]),
           sphere('central_oval_gem',[0,-.48,0],[.73,.32,1.30])]
    return revision(part('dragon-prince-shield',atoms,dict(grip=[0,.5,0]),seed),
                    4,'Dragon Prince symmetrical great shield with central oval gem')


def scaled_shield(seed):
    data=gem_shield(seed).to_dict();p=data['parameters'];extra=[]
    for row in range(-4,5):
        z=row*.53
        for col in range(-2,3):
            x=col*.61
            # Stay within the diamond rim and leave the oval setting exposed.
            if abs(x)/1.856+(abs(z)+.38)/2.681>.92:continue
            if (x/.83)**2+(z/1.12)**2<1.1:continue
            extra.append(dict(role=f'flat_scale_{row}_{col}',primitive='cone',export=False,
                location=[x,-.30,z],radius1=.33,radius2=.27,depth=.32,vertices=4,
                rotation=[math.pi/2,0,0],scale=[1,1.13,1],bevel=.025))
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='shield',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    return revision(ComponentDefinition.from_dict(data),5,'Dragon Prince flat scaled shield with oval gem')


def dense_scaled_shield(seed):
    data=gem_shield(seed).to_dict();p=data['parameters'];extra=[]
    for row in range(-6,7):
        z=row*.35
        for col in range(-4,5):
            x=col*.40
            if abs(x)/1.856+abs(z)/2.681+.25/1.856>.96:continue
            if (x/.65)**2+(z/.99)**2<1.14:continue
            extra.append(dict(role=f'flat_scale_{row}_{col}',primitive='cone',export=False,
                location=[x,-.30,z],radius1=.25,radius2=.215,depth=.32,vertices=4,
                rotation=[math.pi/2,0,0],scale=[1,1.1,1],bevel=.018))
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='shield',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    return revision(ComponentDefinition.from_dict(data),6,'Dragon Prince dense flat scale shield with oval gem')


def flexed_steed(seed):
    data=taller_steed(seed).to_dict();p=data['parameters']
    removed={a['role'] for a in p['atoms'] if any(a['role'].endswith(s) for s in ('_upper','_lower','_knee'))}
    p['atoms']=[a for a in p['atoms'] if a['role'] not in removed]
    p['operations']=[o for o in p['operations'] if o['operand'] not in removed]
    atoms=[]
    for side in (-1,1):
        hip=[side*.78,-1.45,4.4];knee=[side*.98,-2.16,2.2];ankle=[side*1.03,-2.13,.7]
        atoms.extend([link(f'{side}_fore_upper',hip,knee,.44),sphere(f'{side}_fore_knee',knee,[.8,.85,.9]),
                      link(f'{side}_fore_lower',knee,ankle,.31)])
        hip=[side*.78,1.8,4.4];stifle=[side*.95,1.20,3.15]
        hock=[side*1.02,2.78,1.7];ankle=[side*1.03,2.55,.7]
        atoms.extend([link(f'{side}_hind_thigh',hip,stifle,.46),sphere(f'{side}_hind_stifle',stifle,[.83,.85,.86]),
                      link(f'{side}_hind_shin',stifle,hock,.35),sphere(f'{side}_hind_hock',hock,[.65,.72,.72]),
                      link(f'{side}_hind_cannon',hock,ankle,.31)])
    p['atoms'].extend(atoms)
    p['operations'].extend(dict(target='barrel',operand=a['role'],operation='UNION',solver='EXACT') for a in atoms)
    return revision(ComponentDefinition.from_dict(data),4,'Dragon Prince horse with flexed knees and hocks')


def heroic_steed(seed):
    """Fuller cavalry proportions, with the reviewed joint and saddle locations."""
    data=flexed_steed(seed).to_dict();p=data['parameters']
    for i,a in enumerate(p['atoms']):
        role=a['role']
        if role.endswith(('_fore_lower','_hind_cannon')):a['radius']=.43
        elif role.endswith('_fore_upper'):a['radius']=.53
        elif role.endswith('_hind_thigh'):a['radius']=.60
        elif role.endswith('_hind_shin'):a['radius']=.46
        elif role.endswith(('_fore_knee','_hind_stifle','_hind_hock')):
            a['dimensions']=[v*1.22 for v in a['dimensions']]
        elif role.endswith('_hoof'):
            p['atoms'][i]=dict(role=role,primitive='cone',export=False,
                location=[a['location'][0],a['location'][1],.375],radius1=.59,radius2=.49,
                depth=.75,vertices=12,scale=[1,1.20,1],bevel=.07)
        elif role=='shoulders':a['dimensions']=[2.52,2.42,3.04]
        elif role=='haunches':a['dimensions']=[2.72,2.30,2.94]
    extra=[]
    for side in (-1,1):
        extra.extend([
            sphere(f'forearm_muscle_{side}',[side*.91,-1.77,3.25],[1.10,1.18,1.72]),
            sphere(f'hind_thigh_muscle_{side}',[side*.86,1.52,3.75],[1.28,1.42,1.72]),
            sphere(f'hind_calf_{side}',[side*.99,2.01,2.45],[.96,1.22,1.45]),
            sphere(f'fore_fetlock_{side}',[side*1.03,-2.13,.83],[1.0,1.08,.74]),
            sphere(f'hind_fetlock_{side}',[side*1.03,2.55,.83],[1.0,1.08,.74])])
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='barrel',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    p['design_notes']='GW cavalry reference study: muscular upper limbs, 0.86 mm lower legs, prominent joints and rounded broad hooves; original primitive construction.'
    return revision(ComponentDefinition.from_dict(data),5,'Dragon Prince heroic steed with muscular legs and broad hooves')


def scalp_barding(definitions,seed):
    data=upright_helmets(definitions,seed)[1].to_dict();p=data['parameters']
    cap=sphere('fitted_scalp_cap',[0,-3.05,7.7],[1.35,2.42,1.98])
    cut=cube('scalp_lower_trim',[0,-3.05,6.0],[3,4,4.15],0)
    ridge=link('scalp_metal_ridge',[0,-3.65,8.53],[0,-2.65,8.61],.12)
    p['atoms'].extend([cap,cut,ridge])
    p['operations'].extend([
        dict(target=cap['role'],operand=cut['role'],operation='DIFFERENCE',solver='EXACT'),
        dict(target='chamfron',operand=cap['role'],operation='UNION',solver='EXACT'),
        dict(target='chamfron',operand=ridge['role'],operation='UNION',solver='EXACT')])
    return revision(ComponentDefinition.from_dict(data),8,'Dragon Prince fitted horse scalp armor')


def revision(definition, version, name):
    data = definition.to_dict()
    data.update(version=version, name=name)
    return validate_part(ComponentDefinition.from_dict(data))


def fin(role, start, end, width, thickness=.32):
    """Solid tapered metal panel in the YZ plane; no mesh construction."""
    dy, dz = end[1]-start[1], end[2]-start[2]
    return dict(role=role, primitive='cone', export=False,
                location=[(a+b)/2 for a,b in zip(start,end)],
                radius1=width/2, radius2=.055, depth=math.hypot(dy,dz),
                vertices=4, scale=[thickness/width,1,1],
                rotation=[-math.atan2(dy,dz),0,0], bevel=.025)


def elven_steed(seed):
    data=horse(seed).to_dict()
    atoms=data['parameters']['atoms']
    for a in atoms:
        if a['role']=='head': a.update(location=[0,-3.17,7.10],dimensions=[1.18,2.3,1.25])
        if a['role']=='muzzle': a.update(location=[0,-4.1,6.73],dimensions=[1.02,1.45,.85])
    # Overlapping locks form a mane behind the neck and a swept tail.
    extra=[]
    for i in range(5):
        extra.append(sphere(f'mane_lock_{i}',[0,-.72+i*.15,6.85-i*.38],[.68,1.15,.85]))
    extra.extend([sphere('swept_tail',[0,3.38,3.8],[.9,1.65,1.85]),
                  sphere('tail_end',[0,3.78,3.15],[.8,1.0,1.25])])
    atoms.extend(extra)
    data['parameters']['operations'].extend(dict(target='barrel',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    return revision(ComponentDefinition.from_dict(data),2,'Dragon Prince elven steed with flowing mane')


def dragon_barding(seed):
    atoms=[sphere('chamfron',[0,-3.5,7.57],[.98,1.65,.38]),
           cube('armored_nose',[0,-4.14,6.97],[1.13,.65,.53],.13),
           sphere('chest_barding',[0,-2.08,4.65],[2.05,.75,2.2])]
    for side in (-1,1):
        x=side*1.14
        atoms.append(sphere(f'flank_plate_{side}',[x,.45,4.7],[.55,4.7,2.45]))
        # Long layered panels replace the checkerboard scales.
        for i,y in enumerate((-1.05,.0,1.05,2.05)):
            atoms.append(fin(f'flank_panel_{side}_{i}',[side*1.38,y,5.35],
                             [side*1.38,y+.46,3.25 if i<3 else 3.55],1.38,.42))
            atoms.append(link(f'panel_rib_{side}_{i}',[side*1.6,y,5.3],
                              [side*1.6,y+.4,3.6 if i<3 else 3.9],.12))
        # Solid dragon cheek wings and tall brow horns leave the eyes uncovered.
        atoms.append(fin(f'cheek_wing_{side}',[side*.65,-2.76,7.12],
                         [side*.65,-1.8,8.12],1.05,.36))
        atoms.append(fin(f'brow_horn_{side}',[side*.4,-3.0,7.55],
                         [side*.4,-2.62,8.72],.6,.32))
        atoms.append(link(f'bridle_{side}',[side*.59,-4.06,6.7],[side*.6,-2.25,7.4],.13))
        atoms.append(sphere(f'chest_gem_{side}',[side*.72,-2.5,5.25],[.52,.32,.64]))
        for i in range(3):
            atoms.append(fin(f'neck_lame_{side}_{i}',[side*.72,-1.36-i*.32,6.1+i*.4],
                             [side*.72,-1.15-i*.32,5.25+i*.4],.88,.3))
    for i in range(3):
        atoms.append(fin(f'breast_lame_{i}',[0,-2.46,5.2-i*.5],[0,-2.55,4.35-i*.5],1.55,.85))
    return revision(part('dragon-prince-barding',atoms,{},seed),3,'Dragon Prince swept plate and draped barding')


def winged_helmet(parent,seed):
    data=parent.to_dict()
    data.update(component_id='aurelian.dragon-prince-helmet',version=2,
                name='Dragon Prince tall winged metal helmet')
    extra=[]
    for side in (-1,1):
        for i,(y,z,w) in enumerate(((.6,2.75,.85),(1.26,2.05,1.05),(1.62,1.35,.95))):
            extra.append(fin(f'helm_wing_{side}_{i}',[side*.69,.15,.72+i*.03],
                             [side*.69,y,z],w,.4))
            extra.append(link(f'helm_rib_{side}_{i}',[side*.84,.22,.78],
                              [side*.84,y-.05,z-.2],.12))
    extra.append(sphere('forehead_gem',[0,-.8,.98],[.4,.3,.62]))
    data['parameters']['atoms'].extend(extra)
    data['parameters']['operations'].extend(dict(target='helmet_crown',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    data['parameters'].update(seed=seed,parent_reference=parent.reference)
    return validate_part(ComponentDefinition.from_dict(data))


def winged_pauldrons(seed):
    atoms=[]
    for side in (-1,1):
        atoms.append(sphere(f'shoulder_shell_{side}',[side*1.02,0,.83],[1.15,1.4,.9]))
        for i in range(3):
            x=side*(.95+i*.22)
            atoms.append(fin(f'pauldron_wing_{side}_{i}',[x,-.28,.55],
                             [x,.92+i*.1,1.45-i*.2],1.12,.4))
            atoms.append(link(f'pauldron_rim_{side}_{i}',[x,-.28,.61],
                              [x,.82+i*.1,1.35-i*.2],.12))
        atoms.append(sphere(f'shoulder_jewel_{side}',[side*1.05,-.64,.86],[.5,.32,.58]))
    return part('dragon-prince-winged-pauldrons',atoms,{},seed)


def pennant_lance(seed):
    data=lance(seed).to_dict()
    extra=[]
    # A broad supported pennant flowing backward from the top of the shaft.
    for i in range(3):
        a=cube(f'pennant_fold_{i}',[0,.48+i*.62,5.95+(.12 if i==1 else 0)],
               [.35,.85,.72-i*.12],.09)
        a['rotation']=[.12 if i==1 else -.1,0,0]
        extra.append(a)
    data['parameters']['atoms'].extend(extra)
    data['parameters']['operations'].extend(dict(target='shaft',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    return revision(ComponentDefinition.from_dict(data),2,'Dragon Prince lance with flowing pennant')


def reference_parts(definitions,seed):
    return [elven_steed(seed),dragon_barding(seed),winged_helmet(definitions['aurelian.helmet@5'],seed),
            winged_pauldrons(seed),pennant_lance(seed)]


def taller_steed(seed):
    data=elven_steed(seed).to_dict()
    for a in data['parameters']['atoms']:
        role=a['role']
        if role=='head': a.update(location=[0,-3.05,7.65],dimensions=[1.22,2.3,1.85])
        elif role=='muzzle': a['location'][2]+=.45
        elif role.startswith('ear_'): a['location'][2]+=.9
        elif role.startswith('eye_'): a['location'][2]+=.7
    extra=sphere('upper_neck',[0,-2.13,7.12],[1.5,1.9,2.35])
    data['parameters']['atoms'].append(extra)
    data['parameters']['operations'].append(dict(target='barrel',operand=extra['role'],operation='UNION',solver='EXACT'))
    data['parameters']['landmarks']['muzzle'][2]+=.45
    return revision(ComponentDefinition.from_dict(data),3,'Dragon Prince taller upright horse head')


def connected_barding(seed):
    data=dragon_barding(seed).to_dict()
    p=data['parameters']
    removed={a['role'] for a in p['atoms'] if a['role'].startswith(('cheek_wing_','brow_horn_'))}
    p['atoms']=[a for a in p['atoms'] if a['role'] not in removed]
    p['operations']=[o for o in p['operations'] if o['operand'] not in removed]
    for a in p['atoms']:
        if a['role']=='chamfron':
            a.update(location=[0,-3.46,8.02],dimensions=[1.12,2.0,.62])
            c,s=math.cos(-.28),math.sin(-.28)
            a['frame_mm']=[[1,0,0,0],[0,c,-s,-3.46*(1-c)+8.02*s],
                           [0,s,c,8.02*(1-c)+3.46*s],[0,0,0,1]]
        elif a['role']=='armored_nose': a['location'][2]+=.45
        elif a['role'].startswith('bridle_'):
            a['start'][2]+=.45; a['end'][2]+=.7
    extra=[]
    for side in (-1,1):
        # Broad cheek roots join the face plate; swept panels overlap each other.
        extra.append(sphere(f'cheek_root_{side}',[side*.46,-2.73,7.85],[.65,1.12,1.28]))
        extra.append(fin(f'cheek_wing_{side}',[side*.46,-2.85,7.75],
                         [side*.46,-1.52,8.95],1.35,.65))
        extra.append(fin(f'brow_horn_{side}',[side*.38,-3.03,8.04],
                         [side*.38,-2.12,9.54],1.15,.62))
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='chamfron',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    return revision(ComponentDefinition.from_dict(data),5,'Dragon Prince connected swept horse helmet')


def connected_helmet(parent,seed):
    data=winged_helmet(parent,seed).to_dict();p=data['parameters']
    removed={a['role'] for a in p['atoms'] if a['role'].startswith(('helm_wing_','helm_rib_'))}
    p['atoms']=[a for a in p['atoms'] if a['role'] not in removed]
    p['operations']=[o for o in p['operations'] if o['operand'] not in removed]
    extra=[]
    for side in (-1,1):
        extra.append(sphere(f'temple_wing_root_{side}',[side*.52,.26,1.15],[.7,1.35,1.6]))
        for i,(y,z,w) in enumerate(((1.28,2.85,1.45),(1.73,2.05,1.35),(1.8,1.35,1.1))):
            extra.append(fin(f'joined_helm_wing_{side}_{i}',[side*.56,.03,1.0],
                             [side*.56,y,z],w,.72))
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='helmet_crown',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    return revision(ComponentDefinition.from_dict(data),3,'Dragon Prince integrated swept helmet wings')


def raised_reins(seed):
    return revision(part('dragon-prince-reins',[
        link('reins_front',[-.6,-4,7.25],[-1.1,-2.7,7.55],.12),
        link('reins_hand',[-1.1,-2.7,7.55],[-1.5,-1,8.4],.12)],
        dict(bit=[-.6,-4,7.25],grip=[-1.5,-1,8.4]),seed),2,'Reins fitted to taller horse head')


def connected_head_parts(definitions,seed):
    return [taller_steed(seed),connected_barding(seed),connected_helmet(definitions['aurelian.helmet@5'],seed),raised_reins(seed)]


def swept_scale(role,start,end,width,thickness):
    """Broad solid metal scale, with a blunt tapered rear and a planar ridge."""
    a=fin(role,start,end,width,thickness)
    a.update(radius2=width*.24,bevel=.075)
    return a


def scale_helmets(definitions,seed):
    rider=connected_helmet(definitions['aurelian.helmet@5'],seed).to_dict()
    mount=connected_barding(seed).to_dict()
    for data,prefixes,root,version,name in (
        (rider,('temple_wing_root_','joined_helm_wing_'),'helmet_crown',4,'Dragon Prince continuous swept dragon scale helmet'),
        (mount,('cheek_root_','cheek_wing_','brow_horn_'),'chamfron',6,'Horse continuous swept dragon scale helmet')):
        p=data['parameters']
        removed={a['role'] for a in p['atoms'] if a['role'].startswith(prefixes)}
        p['atoms']=[a for a in p['atoms'] if a['role'] not in removed]
        p['operations']=[o for o in p['operations'] if o['operand'] not in removed]
        extra=[]
        for side in (-1,1):
            for i in range(2):
                if root=='helmet_crown':
                    start=[side*(.52+i*.12),-.1,1.05+i*.65]
                    end=[start[0],2.12-i*.12,1.75+i*.65]
                    width,thickness=1.75,.85
                else:
                    start=[side*(.42+i*.13),-3.02,7.92+i*.47]
                    end=[start[0],-1.03-i*.12,8.32+i*.47]
                    width,thickness=1.38,.78
                extra.append(swept_scale(f'swept_scale_{side}_{i}',start,end,width,thickness))
        p['atoms'].extend(extra)
        p['operations'].extend(dict(target=root,operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
        data.update(version=version,name=name)
    return [validate_part(ComponentDefinition.from_dict(d)) for d in (rider,mount)]


def swept_visor(definitions,seed):
    data=upright_helmets(definitions,seed)[0].to_dict();p=data['parameters']
    p['atoms']=[a for a in p['atoms'] if a['role']!='angular_brow']
    p['operations']=[o for o in p['operations'] if o['operand']!='angular_brow']
    for side in (-1,1):
        a=cube(f'swept_brow_{side}',[side*.43,-.70,.79],[1.04,.4,.28],.075)
        a['rotation']=[0,-side*.30,side*.42]
        p['atoms'].append(a)
        p['operations'].insert(-1,dict(target='dragon_crown',operand=a['role'],operation='UNION',solver='EXACT'))
    p['landmarks']['front_brim']=[0,-.89,.65]
    return revision(ComponentDefinition.from_dict(data),6,'Dragon Prince with upswept brow visor')


def upright_scale_panels(prefix, y, z, height, width):
    atoms=[]
    for side in (-1,1):
        for layer in range(2):
            start=[side*.52,y+layer*.42,z-layer*.22]
            end=[side*.52,y+.62+layer*.42,z+height-layer*.42]
            panel=swept_scale(f'{prefix}_plate_{side}_{layer}',start,end,width,.85)
            panel['radius2']=width*.12
            atoms.append(panel)
        # Large overlapping diamond relief on the continuous main plate.
        for row in range(3):
            t=.2+row*.24
            for col in range(2):
                atoms.append(dict(role=f'{prefix}_scale_{side}_{row}_{col}',primitive='cone',export=False,
                    location=[side*(.52+.425*(1-.76*t)),y+.62*t+(col-.5)*.35,z+height*t],
                    radius1=.34,radius2=.28,depth=.27,vertices=4,
                    rotation=[0,side*math.pi/2,0],scale=[1.22,1,1],bevel=.04))
    return atoms


def upright_helmets(definitions,seed):
    # Entirely new crown and cheek plates, built independently of the infantry helmet.
    atoms=[dict(role='dragon_crown',primitive='cone',export=True,location=[0,.12,.65],
                radius1=1.02,radius2=.69,depth=2.35,vertices=8,scale=[1,1.05,1],bevel=.12)]
    for side in (-1,1):
        atoms.append(cube(f'cheek_guard_{side}',[side*.74,-.37,-.24],[.42,1.0,1.25],.12))
    atoms.append(cube('angular_brow',[0,-.79,.62],[1.6,.44,.32],.08))
    atoms.extend(upright_scale_panels('rider',.06,.85,2.55,1.4))
    atoms.append(sphere('brow_gem',[0,-1.0,.85],[.42,.25,.48]))
    rider=part('dragon-prince-helmet',atoms,dict(front_brim=[0,-.79,.62]),seed).to_dict()
    opening=cube('face_opening',[0,-1.03,-.18],[1.16,1.65,1.32],.12)
    rider['parameters']['atoms'].append(opening)
    rider['parameters']['operations'].append(dict(target='dragon_crown',operand='face_opening',operation='DIFFERENCE',solver='EXACT'))
    rider.update(version=5,name='Dragon Prince angular crown with upright overlapping dragon scales')
    mount=connected_barding(seed).to_dict();p=mount['parameters']
    removed={a['role'] for a in p['atoms'] if a['role'].startswith(('cheek_root_','cheek_wing_','brow_horn_'))}
    p['atoms']=[a for a in p['atoms'] if a['role'] not in removed]
    p['operations']=[o for o in p['operations'] if o['operand'] not in removed]
    extra=upright_scale_panels('horse',-2.89,7.87,1.95,1.25)
    p['atoms'].extend(extra)
    p['operations'].extend(dict(target='chamfron',operand=a['role'],operation='UNION',solver='EXACT') for a in extra)
    mount.update(version=7,name='Horse upright layered dragon scale head armor')
    return [validate_part(ComponentDefinition.from_dict(d)) for d in (rider,mount)]
