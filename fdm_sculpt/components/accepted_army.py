"""Propagate the accepted infantry language without changing unit equipment."""
from copy import deepcopy
from math import atan2, degrees, hypot, sqrt

from .elves_v2 import identity, multiply, point
from .readable_infantry import yaw
from .spearman_overhangs import finish, ramp
from .parts import inverse_rigid
from .core import component_digest
from .upper_spear_trial import fill_part

SHARED = {
    'aurelian.head@12': 'aurelian.readable-head-trial@3',
    'aurelian.helmet@5': 'aurelian.readable-helmet-trial@1',
    'aurelian.helmet@7': 'aurelian.readable-helmet-trial@1',
    'aurelian.torso@4': 'aurelian.readable-torso-trial@1',
    'aurelian.chest-plate@4': 'aurelian.readable-chest-plate-trial@1',
    'aurelian.skirt@8': 'aurelian.readable-mail-trial@3',
    'aurelian.shield@2': 'aurelian.shield@6',
    'aurelian.shield-insignia@4': 'aurelian.readable-insignia-trial@4',
    'aurelian.spear@5': 'aurelian.uniform-spear-140-trial@3',
    'aurelian.base-body-4x5-plain@1': 'aurelian.glue-footing@1',
}


def new_part(source, kind):
    data = deepcopy(source.to_dict())
    # Distinct historical source revisions may carry distinct posed geometry.
    data.update(component_id=source.component_id+f'-accepted-r{source.version}', version=1,
                name=source.name+' — accepted infantry detail')
    data['parameters']['accepted_army'] = dict(source=source.reference,
        source_sha256=source.sha256, treatment=kind, seed=1001, print_scale=1.3,
        status='visual-only', accepted_reference='wider-shield-infantry-3-trial')
    return data


def fuller_arm(source):
    data = new_part(source, 'Fuller sleeve and hand, opened elbow, fixed equipment grip')
    p = data['parameters']; landmarks = p['landmarks']
    pose = p.get('cloth_pose', {})
    elbow = pose.get('elbow', landmarks.get('elbow'))
    if elbow is None:
        elbow = next((v for k,v in landmarks.items() if k.endswith('_elbow')), None)
    delta = [0,0,0]
    if elbow:
        length = hypot(elbow[0],elbow[1])
        if length > .01: delta = [.30*elbow[0]/length,.30*elbow[1]/length,0]
    new_elbow = [a+b for a,b in zip(elbow,delta)] if elbow else None
    for i,a in enumerate(p['atoms']):
        role = a['role']
        hand = any(s in role for s in ('palm','fingers','thumb','fist','knuckle'))
        if hand:
            if 'dimensions' in a:a['dimensions']=[v*1.25 for v in a['dimensions']]
            if role.endswith('_additive_taper'):a['radius2']*=1.25
            continue
        if pose and role in ('robe_sleeve','cloth_forearm'):
            start,end = (pose['shoulder'],new_elbow) if role=='robe_sleeve' else (new_elbow,pose['wrist'])
            b = ramp(role,start,end,a['radius1']*1.25,a['radius2']*1.25)
            b.update(export=a['export'],bevel=a.get('bevel',.04))
            p['atoms'][i]=b
            continue
        if elbow and a['primitive']=='between':
            for key in ('start','end'):
                if sum((x-y)**2 for x,y in zip(a[key],elbow))<1e-8:a[key]=list(new_elbow)
        if elbow and 'location' in a:
            frame=a.get('frame_mm',identity());center=point(frame,a['location'])
            distance=sqrt(sum((x-y)**2 for x,y in zip(center,elbow)))
            weight=max(0,1-distance/1.3)
            if 'frame_mm' in a:
                for axis in range(3):a['frame_mm'][axis][3]+=weight*delta[axis]
            else:
                a['location']=[v+weight*d for v,d in zip(a['location'],delta)]
        if role in ('shoulder','cloth_shoulder','elbow','cloth_elbow'):
            a['dimensions']=[v*(1.15 if 'shoulder' in role else 1.25) for v in a['dimensions']]
        if role in ('upper_arm','forearm') and 'radius' in a:a['radius']*=1.25
    if pose:pose['elbow']=new_elbow
    for name in list(landmarks):
        if name=='elbow' or name.endswith('_elbow'):landmarks[name]=new_elbow
    p['accepted_army'].update(hand_factor=1.25,sleeve_factor=1.25,elbow_shift_mm=delta,
                              grip_landmarks_unchanged=True)
    return finish(data)


def broader_body(source):
    data=new_part(source,'15 percent broader body with original unit armour/cloth')
    p=data['parameters']
    for a in p['atoms']:
        # Each primitive remains parameterized, with its rigid local frame.
        if 'dimensions' in a:a['dimensions'][0]*=1.15
        elif a['primitive'] in ('cone','cylinder'):
            a.setdefault('scale',[1,1,1])[0]*=1.15
        for key in ('location','start','end'):
            if key in a:a[key][0]*=1.15
        if 'frame_mm' in a:a['frame_mm'][0][3]*=1.15
    for v in p['landmarks'].values():
        if len(v)==3 and isinstance(v[0],(int,float)):v[0]*=1.15
    return finish(data)


def clearer_helmet(source):
    data=new_part(source,'Broader helmet opening, preserving rank/dragon ornament')
    for a in data['parameters']['atoms']:
        if a['role'] in ('helmet_face_opening','face_opening'):
            a['dimensions']=[max(a['dimensions'][0],1.20),max(a['dimensions'][1],2.3),max(a['dimensions'][2],1.86)];a['bevel']=.08
        elif a['role']=='nape_front_clearance':a['dimensions'][0]=1.20
    return finish(data)


def lance(source, definitions):
    data=new_part(source,'Uniform 1.4 mm shaft and accepted decorative leaf head')
    p=data['parameters'];shaft=next(a for a in p['atoms'] if a['role']=='shaft')
    shaft.update(radius=.7,vertices=64)
    p['atoms']=[a for a in p['atoms'] if a['role']!='point']
    p['operations']=[o for o in p['operations'] if o['operand']!='point']
    for a in p['atoms']:
        if a['role']=='hand_guard':a['radius2']=.71
    # Keep lance shaft endpoints and grip; root the accepted blade on its tip.
    z=shaft['location'][2]+shaft['depth']/2-.08
    for original in definitions['aurelian.uniform-spear-140-trial@3'].to_dict()['parameters']['atoms']:
        if original['role'] not in ('spear_leaf_lower','spear_leaf_tip'):continue
        a=deepcopy(original);a['location'][1]=0;a['location'][2]+=z-7.13
        p['atoms'].append(a)
        p['operations'].append(dict(target='shaft',operand=a['role'],operation='UNION',solver='EXACT'))
    return finish(data)


def decorated_pole(source, definitions):
    data=new_part(source,'Uniform 1.4 mm standard pole with fuller faceted finial')
    p=data['parameters']
    for a in p['atoms']:
        if a['role']=='standard_pole':a['radius']=.7
        elif a['role']=='finial_collar':a.update(radius1=.77,radius2=.72)
        elif a['role']=='leaf_finial_lower':a.update(radius1=.48,radius2=1.05,depth=.85,location=[0,.46,14.575],scale=[1,.575,1],vertices=4,bevel=0)
        elif a['role']=='leaf_finial_tip':a.update(radius1=1.05,radius2=.27,depth=1.75,location=[0,.46,15.875],scale=[1,.575,1],vertices=4,bevel=0)
    return finish(data)


def raised_relief(source):
    data=new_part(source,'Broad flat relief with 0.30 mm source projection')
    p=data['parameters']
    if 'dragon-prince-shield' in source.component_id:
        for a in p['atoms']:
            if a['role']=='shield':a['scale'][0]*=1.12
            elif a['role'].startswith('flat_scale_'):
                a['depth']=.42;a['location'][1]-=.05
    else:
        # Star relief on the standard remains its own insignia.
        for a in p['atoms']:
            if 'dimensions' in a:a['dimensions'][1]*=1.5
            if 'depth' in a:a['depth']+=.10
            if 'location' in a:a['location'][1]-=.05
    return finish(data)


def part_map(sources, definitions):
    mapping=dict(SHARED);parts={}
    for ref in sorted({p['part'] for s in sources.values() for p in s['placements']}):
        if ref in mapping:continue
        source=definitions[ref];name=source.component_id
        if '-arm' in name and any(s in a['role'] for a in source.to_dict()['parameters']['atoms'] for s in ('palm','fist','fingers')):
            part=fuller_arm(source)
        elif name in ('aurelian.archer-tunic','aurelian.swordmaster-cuirass','aurelian.torso'):
            part=broader_body(source)
        elif 'helmet' in name and any(a['role'] in ('helmet_face_opening','face_opening') for a in source.to_dict()['parameters']['atoms']):
            part=clearer_helmet(source)
        elif name=='aurelian.dragon-prince-lance':part=lance(source,definitions)
        elif name=='aurelian.standard-pole':part=decorated_pole(source,definitions)
        elif name in ('aurelian.dragon-prince-shield','aurelian.standard-insignia'):part=raised_relief(source)
        else:continue
        parts[part.reference]=part;mapping[ref]=part.reference
    return mapping,parts


def upgrade(source, mapping, definitions):
    spec=deepcopy(source)
    spec['label']=source.get('label',source['assembly_id'])+' — accepted detail (visual-only)'
    for p in spec['placements']:
        if p['part'] in mapping:
            part=definitions[mapping[p['part']]]
            p.update(part=part.reference,definition_sha256=part.sha256)
    groups={}
    for p in spec['placements']:
        if '/' in p['instance_id']:
            group,slot=p['instance_id'].split('/',1);groups.setdefault(group,{})[slot]=p
    turns=[]
    for group,slots in groups.items():
        if 'shield' not in slots:continue
        shield=slots['shield'];body=slots.get('torso',shield)
        angle=lambda p:degrees(atan2(p['mount'][1][0],p['mount'][0][0]))
        relative=(angle(shield)-angle(body)+180)%360-180
        target=max(-20,min(20,relative));delta=target-relative
        if abs(delta)>1e-6:
            transform=yaw([r[3] for r in shield['mount'][:3]],delta)
            for slot in ('shield','shield-insignia'):
                if slot in slots:slots[slot]['mount']=multiply(transform,slots[slot]['mount'])
        turns.append(dict(figure=group,before_degrees=relative,after_degrees=target))
    return spec,turns


def fitted_spear_joins(spec, definitions):
    """Reuse a local join only for nearby upright spears, never across open poses."""
    groups={};parts={}
    for p in spec['placements']:
        if '/' in p['instance_id']:
            group,slot=p['instance_id'].split('/',1);groups.setdefault(group,{})[slot]=p
    for group,slots in groups.items():
        if not all(s in slots for s in ('right-arm','helmet','spear','torso')):continue
        if 'helmet-spear-fill' in slots:continue
        arm=definitions[slots['right-arm']['part']].to_dict()['parameters']
        if 'right_shoulder_slope' not in arm['landmarks']:continue
        spear=slots['spear'];helmet=slots['helmet']
        if spear['mount'][2][2]<.94:continue
        h=point(helmet['mount'],[.50,.24,.12]);s=point(spear['mount'],[0,.46,0])
        direction=[r[2] for r in spear['mount'][:3]]
        t=(h[2]-s[2])/direction[2]
        distance=sqrt(sum((s[i]+t*direction[i]-h[i])**2 for i in range(3)))
        if distance>2.5:continue
        mount=slots['torso']['mount'];inverse=inverse_rigid(mount)
        local=[dict(p,mount=multiply(inverse,p['mount'])) for p in slots.values()]
        data=fill_part(dict(placements=local),definitions,1).to_dict()
        key=component_digest(data['parameters'])[:12]
        data.update(component_id='aurelian.accepted-helmet-join-'+key,version=1)
        part=finish(data);parts[part.reference]=part
        spec['placements'].append(dict(instance_id=group+'/helmet-spear-fill',part=part.reference,
            definition_sha256=part.sha256,mount=deepcopy(mount)))
    return parts
