"""Taller capped feather plumes and rising undersides for short-sword guards."""
from copy import deepcopy
import math

from .elves_v2 import multiply, translation
from .shield_tuck import halfspace
from .spearman_overhangs import finish


def revised_parts(definitions, manifest, seed):
    if type(seed) is not int or seed != manifest['seed']:
        raise ValueError('seed must match the pinned crown and hilt manifest')
    result=[]
    for item in manifest['helmets']:
        source=definitions[item['source']]
        if source.sha256!=item['sha256']:raise ValueError('pinned crown source changed')
        data=deepcopy(source.to_dict());p=data['parameters']
        tip=next(a for a in p['atoms'] if a['role']=='helmet_tapered_tip')
        tip['depth']+=manifest['crown_raise_mm']
        tip['location'][2]+=manifest['crown_raise_mm']/2
        tip.update(radius2=manifest['crown_terminal_radius_mm'],bevel=.03)
        p['landmarks']['helmet_tapered_tip'][2]+=manifest['crown_raise_mm']/2
        p['crown_height_fit']=dict(source=source.reference,source_sha256=source.sha256,
                                  seed=seed,raise_mm=manifest['crown_raise_mm'],
                                  terminal_radius_mm=manifest['crown_terminal_radius_mm'])
        p['provenance']+=' Central crown peak raised 0.60 mm with a broad flat frustum cap; lower crown, nape and face opening preserved. Visual-only.'
        data.update(version=item['version'],name=source.name+' with taller capped crown')
        result.append(finish(data))
    if 'plume' in manifest:
        item=manifest['plume'];source=definitions[item['source']]
        if source.sha256!=item['sha256']:raise ValueError('pinned plume source changed')
        data=deepcopy(source.to_dict());p=data['parameters']
        atoms={a['role']:a for a in p['atoms']}
        factor=item['length_factor']
        for atom in p['atoms']:
            if '_wing_feather_' not in atom['role'] or atom['primitive']!='sphere':continue
            length=atom['dimensions'][2];matrix=atom['frame_mm']
            axis=[matrix[i][2] for i in range(3)]
            root=[atom['location'][i]-axis[i]*length/2 for i in range(3)]
            length*=factor
            center=[root[i]+axis[i]*length/2 for i in range(3)]
            rotation=[row[:3]+[0] for row in matrix[:3]]+[[0,0,0,1]]
            atom.update(location=center,
                        frame_mm=multiply(translation(center),multiply(rotation,translation([-v for v in center]))))
            atom['dimensions'][2]=length
            vertical_radius=math.sqrt(sum((rotation[2][i]*atom['dimensions'][i]/2)**2 for i in range(3)))
            top=center[2]+p['feather_tip_height_fraction']*vertical_radius
            atoms[atom['role']+'_tip_limit']['location'][2]=top-6
        p['plume_height_fit']=dict(source=source.reference,source_sha256=source.sha256,
                                   seed=seed,length_factor=factor)
        p['provenance']+=' Wing feathers lengthened 35 percent from fixed roots, retaining the broad stock and Exact tip cutoff. Central helmet peak unchanged. Visual-only.'
        data.update(version=item['version'],name='Sergeant helmet with taller capped feather plumes')
        result.append(finish(data))
    item=manifest['sword'];source=definitions[item['source']]
    if source.sha256!=item['sha256']:raise ValueError('pinned sword source changed')
    data=deepcopy(source.to_dict());p=data['parameters']
    if manifest.get('readable_hilt'):
        # Leave a visible cylindrical handle above the fist. The narrower
        # guard grows only from its upper end, instead of webbing the whole grip.
        lift=.55
        for atom in p['atoms']:
            if atom['role'] in ('blade_guard','blade_body') or (atom['role']=='blade_point' and manifest.get('raise_blade_point')):
                atom['location'][2]+=lift
        guard=next(a for a in p['atoms'] if a['role']=='blade_guard')
        guard['dimensions']=[1.5,.7,.3]
        grip=next(a for a in p['atoms'] if a['role']=='blade_grip')
        grip.update(depth=1.8,location=[0,0,.6])
        pommel=next(a for a in p['atoms'] if a['role']=='blade_pommel')
        pommel['location'][2]=-.25
        p['landmarks']['pommel']=list(pommel['location'])
        for key in ('guard','tip'):p['landmarks'][key][2]+=lift
        p['atoms'].append(dict(role='guard_upper_collar',primitive='cone',export=False,
                               radius1=.4,radius2=.75,depth=.85,vertices=48,
                               scale=[1,.7/1.5,1],location=[0,0,1.125],bevel=.02))
        p['operations'].append(dict(target='blade_grip',operand='guard_upper_collar',operation='UNION',solver='EXACT'))
        p['design'].update(grip_length_mm=1.8,overall_length_mm=p['design']['overall_length_mm']-.77+lift,
                          note='Visible cylindrical handle with a narrower rising upper guard collar.')
        p['hilt_fit']=dict(source=source.reference,source_sha256=source.sha256,seed=seed,
                           readable_hilt=True,blade_raise_mm=lift,guard_width_mm=1.5,
                           root_z_mm=.7,guard_z_mm=1.55,side_growth_per_height=.35/.85,
                           pommel_raise_mm=.77)
        p['provenance']+=' Cylindrical handle exposed above the fist; narrower guard rises from an upper collar, with no full-height grip web. Visual-only.'
        data.update(version=item['version'],name='Short sword with exposed handle and narrow rising guard')
        result.append(finish(data))
        return result
    if manifest.get('pommel_raise_mm'):
        grip=next(a for a in p['atoms'] if a['role']=='blade_grip')
        grip.update(depth=1.25,location=[0,0,.325])
        pommel=next(a for a in p['atoms'] if a['role']=='blade_pommel')
        pommel['location'][2]+=manifest['pommel_raise_mm']
        p['landmarks']['pommel']=list(pommel['location'])
        p['design'].update(grip_length_mm=1.25,
                           overall_length_mm=p['design']['overall_length_mm']-manifest['pommel_raise_mm'])
        p['design']['note']='Broad straight blade and rising guard; lower hilt shortened to seat the pommel into the fist heel.'
    bottom,top=manifest.get('guard_root_z_mm',-.75),1.03
    root_half_width=manifest.get('guard_root_width_mm',.5)/2
    width,depth=1.85,.8
    target='guard_rising_underside'
    atoms=[dict(role=target,primitive='cube',export=False,bevel=.02,
                location=[0,0,(bottom+top)/2],dimensions=[width,depth,top-bottom])]
    sx=(width/2-root_half_width)/(1-bottom)
    sy=(depth/2-.20)/(1-bottom)
    atoms.extend([
        halfspace('guard_left_rise',[-root_half_width,0,bottom],[1,0,sx]),
        halfspace('guard_right_rise',[root_half_width,0,bottom],[-1,0,sx]),
        halfspace('guard_front_rise',[0,-.20,bottom],[0,1,sy]),
        halfspace('guard_rear_rise',[0,.20,bottom],[0,-1,sy]),
    ])
    p['atoms'].extend(atoms)
    p['operations'].extend(dict(target=target,operand=a['role'],operation='INTERSECT',solver='EXACT') for a in atoms[1:])
    p['operations'].append(dict(target='blade_grip',operand=target,operation='UNION',solver='EXACT'))
    p['hilt_fit']=dict(source=source.reference,source_sha256=source.sha256,seed=seed,
                       root_z_mm=bottom,guard_z_mm=1,side_growth_per_height=sx)
    if manifest.get('pommel_raise_mm'):
        p['hilt_fit']['pommel_raise_mm']=manifest['pommel_raise_mm']
    p['provenance']+=' Exact-cut rising guard underside grows from inside the grip and backs both quillons. Visual-only.'
    data.update(version=item['version'],name='Short sword with rising guard underside')
    result.append(finish(data))
    return result
