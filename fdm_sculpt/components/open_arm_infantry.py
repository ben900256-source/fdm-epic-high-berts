"""Fuller opened arms and tapered detail for the readable infantry study."""
from copy import deepcopy
from math import pi, sqrt

from .core import ComponentDefinition
from .elves_v2 import identity, point
from .parts import validate_part
from .spearman_overhangs import finish, ramp
from .cloth_robes import ellipsoid, operation
from .upper_spear_trial import fill_part


def translated(atom, delta):
    atom = deepcopy(atom)
    if 'frame_mm' in atom:
        for i in range(3): atom['frame_mm'][i][3] += delta[i]
    else:
        atom['location'] = [a+b for a,b in zip(atom['location'],delta)]
    return atom


def fuller_arm(source, side, index, mount):
    data = deepcopy(source.to_dict())
    data.update(component_id=f'aurelian.open-{side}-arm-{index}-trial',version=1,
                name=f'Fuller {side} sleeve with outward elbow and hand, pose {index}')
    old = data['parameters']; sign = 1 if side=='right' else -1
    # Keep the world Z of the hand and held equipment unchanged.
    delta = [mount[0][j]*sign*.50 for j in range(3)]
    elbow_delta = [mount[0][j]*sign*.70 for j in range(3)]
    shoulder = list(old['cloth_pose']['shoulder'])
    elbow = [a+b for a,b in zip(old['cloth_pose']['elbow'],elbow_delta)]
    wrist = [a+b for a,b in zip(old['cloth_pose']['wrist'],delta)]
    p = dict(atoms=[],operations=[],landmarks=deepcopy(old['landmarks']),seed=1001,
             source=source.reference,source_sha256=source.sha256,
             cloth_pose=dict(shoulder=shoulder,elbow=elbow,wrist=wrist),
             arm_trial=dict(sleeve_diameter_factor=1.25,hand_world_shift_mm=sign*.50,
                            elbow_world_shift_mm=sign*.70,print_scale=1.3,status='visual-only'))
    body = ramp('robe_sleeve',shoulder,elbow,.39*1.25,.53*1.25)
    body.update(bevel=.06,bevel_segments=3);p['atoms'].append(body)
    def join(atom,kind='UNION'):
        atom['export']=False;p['atoms'].append(atom)
        p['operations'].append(operation('robe_sleeve',atom['role'],kind))
    join(dict(role='cloth_shoulder',primitive='sphere',location=shoulder,
              dimensions=[.98,.98,.85],segments=32,ring_count=24))
    fore = ramp('cloth_forearm',elbow,wrist,.53*1.25,.33*1.25)
    fore.update(bevel=.06,bevel_segments=3);join(fore)
    join(dict(role='cloth_elbow',primitive='sphere',location=elbow,
              dimensions=[1.30,1.30,1.40],segments=32,ring_count=24))
    root=[sign*.85,elbow[1],elbow[2]-1.5]
    join(ramp('lower_cloth_drape',root,elbow,.24,.58))
    # Deliberate ascending envelope clips the projecting elbow underside.
    join(dict(role='sleeve_rising_envelope',primitive='cone',location=[root[0],root[1],root[2]+3],
              radius1=.24,radius2=5.34,depth=6,vertices=64,bevel=0),'INTERSECT')
    for n,offset in enumerate((-.20,.20)):
        start=[shoulder[0]+offset,shoulder[1]-.36,shoulder[2]-.1]
        end=[elbow[0]+offset,elbow[1]-.53,elbow[2]+.15]
        join(ellipsoid(f'upper_cloth_gather_{n}',start,end,.23,.25))
    # Original hands and their additive cuff tapers move together, without scaling grips.
    hand_roles={a['role'] for a in old['atoms'] if any(t in a['role'] for t in ('palm','fingers','thumb','knuckle_plate'))}
    for atom in old['atoms']:
        if atom['role'] in hand_roles:p['atoms'].append(translated(atom,delta))
    p['operations'].extend(deepcopy(op) for op in old['operations'] if op['target'] in hand_roles and op['operand'] in hand_roles)
    for key,v in p['landmarks'].items():
        if any(t in key for t in ('cuff','palm','fingers','thumb','knuckle','wrist')):
            p['landmarks'][key]=[a+b for a,b in zip(v,delta)]
    p['landmarks'][side+'_elbow']=elbow
    p['landmarks']['drape_root']=root
    data['parameters']=p
    return finish(data)


def supported_details(definitions):
    parts=[]
    source=definitions['aurelian.readable-head-trial@1'];data=deepcopy(source.to_dict())
    data.update(version=2,name='Bold elven face with ascending nose underside')
    p=data['parameters']
    p['atoms'].append(dict(role='nose_rising_envelope',primitive='cone',export=False,
                          location=[0,-.67,.45],radius1=.06,radius2=1.66,depth=2,vertices=64,bevel=0))
    index=next(i for i,o in enumerate(p['operations']) if o['operand']=='nose_bridge')
    p['operations'].insert(index,operation('nose_bridge','nose_rising_envelope','INTERSECT'))
    p['underside_trial']=dict(source=source.reference,source_sha256=source.sha256,
                              lateral_growth_per_height=.8,status='visual-only')
    parts.append(finish(data))

    source=definitions['aurelian.readable-mail-trial@1'];data=deepcopy(source.to_dict())
    data.update(version=3,name='Coarse mail with pointed recess roofs')
    p=data['parameters']
    for atom in p['atoms']:
        if atom['role'].endswith('_eye'):
            atom.update(primitive='cube',dimensions=[.32/sqrt(2),.85,.32/sqrt(2)],
                        rotation=[0,pi/4,0],bevel=.012)
            atom.pop('segments',None);atom.pop('ring_count',None)
    p['chainmail']['eye_profile']='diamond roof, nominal 45 degrees in part frame'
    p['underside_trial']=dict(source=source.reference,source_sha256=source.sha256,status='visual-only')
    parts.append(finish(data))

    source=definitions['aurelian.readable-insignia-trial@1'];data=deepcopy(source.to_dict())
    data.update(version=2,name='Bold seahorse with longer shield-rooted underside ramps')
    p=data['parameters']
    for i,atom in enumerate(p['atoms']):
        if not atom['role'].endswith('_underside'):continue
        frame=atom.get('frame_mm',identity())
        top=point(frame,[0,0,atom['depth']/2])
        x,y=atom['scale'][:2]
        vertical=max(atom['depth']*1.6,1.15*(abs(top[1]+.4)+max(x,y)))
        new=ramp(atom['role'],[top[0],-.40,top[2]-vertical],top,.05,1)
        new['scale']=[x,y,1];p['atoms'][i]=new
    p['underside_trial']=dict(source=source.reference,source_sha256=source.sha256,
                              root_y_mm=-.40,status='visual-only')
    parts.append(finish(data))
    return parts


def build(figures,definitions):
    parts=supported_details(definitions);detail=dict(zip(('head','skirt','shield-insignia'),parts))
    specs=[];gallery=[]
    for index,source in enumerate(figures,1):
        spec=deepcopy(source)
        spec.update(assembly_id=f'open-arm-infantry-{index}-trial',label=f'Fuller open arms and tapered detail, pose {index} (visual-only)')
        slots={p['instance_id'].split('/')[-1]:p for p in spec['placements']}
        for slot,part in detail.items():slots[slot].update(part=part.reference,definition_sha256=part.sha256)
        for side in ('left','right'):
            placement=slots[side+'-arm'];source_arm=definitions[placement['part']]
            arm=fuller_arm(source_arm,side,index,placement['mount']);parts.append(arm)
            placement.update(part=arm.reference,definition_sha256=arm.sha256)
            shift=.50 if side=='right' else -.50
            equipment=('spear',) if side=='right' else ('shield','shield-insignia','shield-torso-connector','shield-lower-connector')
            for slot in equipment:slots[slot]['mount'][0][3]+=shift
        expanded=dict(definitions);expanded.update({p.reference:p for p in parts})
        fill=fill_part(spec,expanded,index).to_dict()
        fill.update(component_id=f'aurelian.open-arm-helmet-fill-{index}-trial',version=1)
        fill=validate_part(ComponentDefinition.from_dict(fill));parts.append(fill)
        slots['helmet-spear-fill'].update(part=fill.reference,definition_sha256=fill.sha256,mount=identity())
        specs.append(spec)
        for placement in spec['placements']:
            q=deepcopy(placement);q['mount'][0][3]+=(index-3)*10;gallery.append(q)
    specs.append(dict(schema_version=1,assembly_id='open-arm-infantry-gallery-trial',
                      label='Fuller opened arms and tapered detail (visual-only)',placements=gallery))
    comparison=[]
    for source,x,prefix in ((figures[2],-4,'before'),(specs[2],4,'after')):
        for placement in source['placements']:
            q=deepcopy(placement);q['instance_id']=prefix+'/'+q['instance_id'].split('/')[-1]
            q['mount'][0][3]+=x;comparison.append(q)
    specs.append(dict(schema_version=1,assembly_id='open-arm-infantry-comparison-trial',
                      label='Close arms / fuller opened arms (visual-only)',placements=comparison))
    return parts,specs
