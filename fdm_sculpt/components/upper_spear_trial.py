"""Thicker upper spears and shoulder-to-helmet fill, without editing reviewed parts."""
from copy import deepcopy
from math import sqrt

from .core import ComponentDefinition
from .elves_v2 import identity
from .parts import validate_part


def point(m,p):
    return [sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3)]


def norm(v):
    length=sqrt(sum(x*x for x in v))
    return [x/length for x in v]


def cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


def thicker_spear(source):
    data=deepcopy(source.to_dict())
    data.update(component_id='aurelian.upper-spear-160-trial',version=1,
                name='Upper spear 1.6 mm source diameter, with fuller spearhead')
    p=data['parameters']
    p['atoms'].extend([
        dict(role='upper_transition',primitive='cone',radius1=.6,radius2=.8,depth=.8,
             location=[0,.46,.2],vertices=48,bevel=0,export=False),
        dict(role='upper_shaft',primitive='cylinder',radius=.8,depth=6.65,
             location=[0,.46,3.875],vertices=48,bevel=.03,export=False)])
    p['operations'].extend(dict(target='spear',operand=role,operation='UNION',solver='EXACT')
                           for role in ('upper_transition','upper_shaft'))
    for atom in p['atoms']:
        if atom['role']=='spear_leaf_lower':atom.update(radius1=.78,radius2=.98)
        if atom['role']=='spear_leaf_tip':atom.update(radius1=.98,radius2=.42)
        if atom['role']=='spear_collar_ramp':atom.update(radius1=.78,radius2=.88)
        if atom['role']=='spear_collar_band':atom.update(radius1=.88,radius2=.88)
    p['design'].update(upper_shaft_diameter_mm=1.6,lower_shaft_diameter_mm=1.2,
                       note='Experimental upper enlargement; original spear axis, length and lower shaft retained.')
    p['experiment']=dict(source=source.reference,source_sha256=source.sha256,print_scale=1.3,
                         printed_upper_diameter_mm=2.08,printed_lower_diameter_mm=1.56)
    return validate_part(ComponentDefinition.from_dict(data))


def fill_part(spec,definitions,index):
    by_slot={p['instance_id'].split('/')[-1]:p for p in spec['placements']}
    arm,helmet,spear=(by_slot[s] for s in ('right-arm','helmet','spear'))
    shoulder=definitions[arm['part']].to_dict()['parameters']['landmarks']['right_shoulder_slope']
    root=point(arm['mount'],shoulder);root[2]-=.35
    head=point(helmet['mount'],[.50,.24,.12])
    shaft0=point(spear['mount'],[0,.46,0])
    shaft_dir=[r[2] for r in spear['mount'][:3]]
    spear_top=[shaft0[i]+shaft_dir[i]*(head[2]-shaft0[2])/shaft_dir[2] for i in range(3)]
    top=[(head[i]+spear_top[i])/2 for i in range(3)]
    axis=[top[i]-root[i] for i in range(3)];length=sqrt(sum(v*v for v in axis));z=norm(axis)
    across=[spear_top[i]-head[i] for i in range(3)]
    x=norm([across[i]-z[i]*sum(across[j]*z[j] for j in range(3)) for i in range(3)])
    y=cross(z,x)
    major=sqrt(sum(v*v for v in across))/2+.30
    frame=identity()
    for i in range(3):
        frame[i][:3]=[x[i],y[i],z[i]]
        frame[i][3]=(root[i]+top[i])/2
    cap=deepcopy(frame)
    for i in range(3):cap[i][3]=top[i]
    atoms=[dict(role='shoulder_fill',primitive='cone',radius1=.32,radius2=1,depth=length,
                scale=[major,.42,1],location=[0,0,0],frame_mm=frame,vertices=48,bevel=0,export=True),
           dict(role='rounded_fill_top',primitive='sphere',dimensions=[2*major,.84,.42],
                location=[0,0,0],frame_mm=cap,segments=40,ring_count=24,export=False)]
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id=f'aurelian.spear-helmet-fill-{index}-trial',version=1,
        name=f'Rounded shoulder and helmet-side spear connection, pose {index}',family='equipment-join',
        required_anchors=['mount'],semantic_slots=['mono'],output_roles=['shoulder_fill'],
        parameters=dict(atoms=atoms,operations=[dict(target='shoulder_fill',operand='rounded_fill_top',operation='UNION',solver='EXACT')],
                        landmarks=dict(mount=[0,0,0],shoulder_root=root,helmet_contact=head,spear_contact=spear_top),
                        seed=1001,experiment=dict(print_scale=1.3,minimum_top_thickness_mm=1.092,
                            source_parts={p['part']:p['definition_sha256'] for p in (arm,helmet,spear)},
                            intent='Fill the shoulder-to-helmet-side gap with a rising rounded volume that also joins the spear.')))))


def build(figures,definitions):
    original=next(p['part'] for p in figures[0]['placements'] if p['instance_id'].endswith('/spear'))
    spear=thicker_spear(definitions[original]);parts=[spear];specs=[]
    gallery=[]
    for i,source in enumerate(figures,1):
        spec=deepcopy(source)
        spec.update(assembly_id=f'upper-spear-fill-{i}-trial',label=f'2.08 mm upper spear and helmet fill, pose {i}')
        for p in spec['placements']:
            if p['instance_id'].endswith('/spear'):p.update(part=spear.reference,definition_sha256=spear.sha256)
        if i==1:
            control=deepcopy(spec);control.update(assembly_id='upper-spear-thick-only-trial',label='Comparison: 2.08 mm upper spear only')
        fill=fill_part(source,definitions,i);parts.append(fill)
        spec['placements'].append(dict(instance_id=f'row-{i:02}/helmet-spear-fill',part=fill.reference,
                                       definition_sha256=fill.sha256,mount=identity()))
        specs.append(spec)
        for p in spec['placements']:
            q=deepcopy(p);q['mount'][0][3]+=(i-3)*10;gallery.append(q)
    specs.append(control)
    specs.append(dict(schema_version=1,assembly_id='upper-spear-fill-gallery-trial',
                      label='Upper spear and helmet fill experiment (source scale)',placements=gallery))
    return parts,specs
