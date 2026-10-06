"""Chariot-specific revisions prompted by the 2026-10-06 deposited-layer audit.

Keep reviewed infantry and cavalry definitions immutable. All added stock is
native primitive geometry; local joins use ordered Exact unions.
"""
from copy import deepcopy
import json
import math
from pathlib import Path

from .core import ComponentDefinition
from .parts import validate_part
from .elves_v2 import multiply, rotation, translation
from .refined_horse import refined_steed_v7, _chain
from .army_expansion import (PREFIX, supported_chariot, coat, chariot_spear_arms,
                             character_arms, character_details, sword, taper, long_shape)


def finish(data, name, seed, notes):
    data['component_id'] = PREFIX + name
    data['name'] = name.replace('-', ' ').capitalize()
    data['family'] = 'army-expansion-' + name
    p = data['parameters']
    p.update(seed=seed, visual_only=True, export_scale=1.3,
             design_notes=notes, audit_source='docs/chariots-sliced-overhang-review.md')
    data['output_roles'] = [a['role'] for a in p['atoms'] if a.get('export')]
    return validate_part(ComponentDefinition.from_dict(data))


def square_taper(role, center, bottom_z, top_z, bottom_width, top_width, depth_ratio=1):
    return dict(role=role, primitive='cone', export=False, location=[0,0,0],
                radius1=bottom_width/math.sqrt(2), radius2=top_width/math.sqrt(2),
                depth=top_z-bottom_z, vertices=4, bevel=0, scale=[1,depth_ratio,1],
                frame_mm=multiply(translation([*center,(bottom_z+top_z)/2]),rotation([0,0,45])))


def union(data, target, atom):
    atom['export'] = False
    data['parameters']['atoms'].append(atom)
    data['parameters']['operations'].append(dict(target=target, operand=atom['role'], operation='UNION', solver='EXACT'))


def chassis(seed):
    data=supported_chariot(seed).to_dict();data['version']=3
    p=data['parameters'];atoms={a['role']:a for a in p['atoms']}
    hull=square_taper('tapered_underbody',[0,3.5],-.10,2.42,3.0,5.55,6.0/5.55)
    atoms['tapered_underbody'].clear();atoms['tapered_underbody'].update(hull)
    p['underbody']=dict(bottom_z_mm=-.10,top_z_mm=2.42,lower_width_mm=3.0,
        upper_width_mm=5.55,upper_length_mm=6.0,front_edge_y_mm=.5,
        face_angle_from_vertical_degrees=math.degrees(math.atan(1.5/2.52)))
    return finish(data,'chariot',seed,'Extended underbody reaches the front board and fluting roots. Deck top and all mounts remain fixed; solid wheel webs retained.')


def driver_coat(seed):
    data=coat(seed).to_dict();data['version']=1
    union(data,'belt',square_taper('belt_underside',[0,-.02],-1.85,-.70,1.12,2.18,1.42/2.18))
    return finish(data,'chariot-driver-coat',seed,'Tapered lower coat grows from the hips into the belt. Upper coat, folds and crew position preserved.')


def arms(kind, seed):
    data=(chariot_spear_arms(seed) if kind=='spear' else character_arms(kind,seed)).to_dict()
    data['version']=2 if kind=='spear' else 1
    p=data['parameters']
    for atom in p['atoms']:
        if atom['role'].startswith('palm_'):
            atom['primitive']='sphere';atom.pop('bevel',None)
            atom.update(segments=48,ring_count=32)
    if kind=='spear':
        grip=p['landmarks']['right_grip']
        union(data,'palm_1',square_taper('grip_underside',grip[:2],grip[2]-1.4,grip[2]-.25,.35,1.92,1.90/1.92))
    return finish(data,'chariot-'+kind+'-arms',seed,'Rounded palm undersides remove the broad flat starting ledges; grip and shoulder landmarks preserved. Spear palm includes stock growing from the shaft.')


def mage_robe(seed):
    data=character_details('mage',seed).to_dict();data['version']=1
    p=data['parameters']
    for i,atom in enumerate(p['atoms']):
        if atom['role']=='robe':
            p['atoms'][i]=dict(taper('robe',[0,.05,-5.52],[0,.05,-.8],1.62,.99,depth=.72),export=True)
        elif atom['role'].startswith('robe_fold_'):
            x=(int(atom['role'].rsplit('_',1)[1])-3)*.38
            p['atoms'][i]=dict(long_shape(atom['role'],[x*.66,-.65,-.8],[x,-.95,-5.35],.27,.27),export=True)
    p['hem_bottom_z_mm']=-5.52
    return finish(data,'chariot-mage-regalia',seed,'Full robe reaches into the deck; the hem and folds start on solid stock. Existing book, collar and upper mantle retained.')


def command_sword(seed):
    data=sword(seed).to_dict();data['version']=1
    p=data['parameters'];atoms={a['role']:a for a in p['atoms']}
    atoms['blade'].update(radius2=.42,scale=[1,.9,1])
    atoms['tip'].update(radius1=.43,radius2=.25,scale=[1,.9,1],depth=.84)
    atoms['tip']['export']=False
    p['operations'].append(dict(target='blade',operand='tip',operation='UNION',solver='EXACT'))
    p['terminal_minimum_depth_mm']=.45
    return finish(data,'chariot-command-sword',seed,'Continuous fuller diamond blade and overlapping finite terminal cap; chariot weapons only. Grip and overall weapon pose preserved.')


def spear(seed):
    path=Path(__file__).parent/'parts/aurelian.uniform-spear-140-trial@3.json'
    data=json.loads(path.read_text(encoding='utf-8'));data['version']=1
    p=data['parameters']
    for atom in p['atoms']:
        if atom['role']=='spear_leaf_tip':atom['radius2']=.42
    p['decorative_blade'].update(terminal_width_mm=.84,terminal_depth_mm=.483,
        source='aurelian.uniform-spear-140-trial@3',note='Chariot-only finite tip enlargement; uniform 1.4 mm shaft and blade outline below terminal taper retained.')
    return finish(data,'chariot-spear',seed,'Fuller terminal cap for the 18-degree chariot pose. Locked infantry spear, uniform shaft, hand axis and deck seat remain unchanged.')


def horse(seed):
    data=refined_steed_v7(seed).to_dict();data['version']=1;p=data['parameters']
    for side in (-1,1):
        tag=f'{side}_hind'
        removed={a['role'] for a in p['atoms'] if a['role'].startswith(tag+'_') and not a['role'].endswith('_hoof')}
        p['atoms']=[a for a in p['atoms'] if a['role'] not in removed]
        p['operations']=[o for o in p['operations'] if o['operand'] not in removed]
        nodes=deepcopy(p['leg_paths'][tag]);shift=-.28*side
        nodes[1][0][1]=1.60+shift*.25
        nodes[2][0][1]=2.28+shift*.6
        p['leg_paths'][tag]=nodes
        for atom in _chain(tag,nodes):
            if atom['primitive']=='sphere':atom.update(segments=64,ring_count=40)
            if atom['primitive']=='cone':atom['vertices']=64
            union(data,'barrel',atom)
    return finish(data,'chariot-horse',seed,'Hind hocks straighten locally beneath the thighs to reduce unsupported inner leg contours. Hooves, stance endpoints, saddle, head and forelegs preserved.')


def chassis_v4(seed):
    data=chassis(seed).to_dict();data['version']=4
    p=data['parameters'];atoms={a['role']:a for a in p['atoms']}
    hull=atoms['tapered_underbody'];hull.update(radius2=6.0/math.sqrt(2),scale=[1,1,1])
    # Clip an axis-aligned square frustum to the rectangular footprint. Scaling
    # a diamond before its 45-degree rotation would instead skew its corners.
    from .spearmen import cube
    clip=dict(cube('underbody_width_clip',[0,3.5,1.15],[5.55,6.2,2.9],0),export=False)
    p['atoms'].append(clip)
    at=next(i for i,o in enumerate(p['operations']) if o['operand']=='tapered_underbody')
    p['operations'].insert(at,dict(target='tapered_underbody',operand=clip['role'],operation='INTERSECT',solver='EXACT'))
    return finish(data,'chariot',seed,'Rectangular clipped underbody reaches the entire front lip; no corner skew. Deck top, solid wheels and mounts preserved.')


def driver_coat_v2(seed):
    data=driver_coat(seed).to_dict();data['version']=2;p=data['parameters']
    next(a for a in p['atoms'] if a['role']=='belt_underside')['scale']=[1,1,1]
    from .spearmen import cube
    clip=dict(cube('coat_depth_clip',[0,-.02,-1.25],[2.4,1.42,1.6],0),export=False)
    p['atoms'].append(clip)
    p['operations'].insert(0,dict(target='belt_underside',operand=clip['role'],operation='INTERSECT',solver='EXACT'))
    return finish(data,'chariot-driver-coat',seed,'Clipped rectangular lower-coat taper supports the complete belt edge and grows from the hips.')


def horse_v2(seed):
    data=horse(seed).to_dict();data['version']=2
    for atom in data['parameters']['atoms']:
        if atom['primitive']=='sphere':atom.update(segments=40,ring_count=24)
        if atom['primitive'] in ('cone','cylinder'):atom['vertices']=40
    data['parameters']['circumferential_segments']=40
    return finish(data,'chariot-horse',seed,'Steeper hind hocks with original planted endpoints; 40-sided rounded primitives give sub-layer surface sampling at print scale. Shared cavalry horse remains pinned.')


def belly_blends(seed):
    from .army_expansion import definition
    atoms=[]
    for side in (-1,1):
        fore_shift=.30*side;hind_shift=-.28*side
        for tag,root,top in [
            ('fore',[side*1.03,-2.13+fore_shift,.99],[side*.45,-.45,3.80]),
            ('hind',[side*1.03,2.55+hind_shift,.99],[side*.45,.75,3.65])]:
            atoms.extend(_chain(f'belly_blend_{side}_{tag}',[(root,.43),(top,.85)]))
    return definition('chariot-horse-belly-blends',atoms,seed,
        notes='Fuller inner chest and haunch planes rise from the planted legs into the belly. Closed anatomical stock prevents the barrel starting as an isolated island; cached horse body remains separate in visual review.')


def chassis_v5(seed):
    data=chassis_v4(seed).to_dict();data['version']=5;p=data['parameters']
    a={atom['role']:atom for atom in p['atoms']}
    hull=a['tapered_underbody'];hull['radius2']=6.7/math.sqrt(2);hull['frame_mm'][1][3]=3.65
    a['underbody_width_clip'].update(location=[0,3.475,1.15],dimensions=[5.55,6.05,2.9])
    # Bury the round wheel contact patches in the base so their first exposed
    # layers grow from a broad footprint rather than a mathematical tangent.
    for side in (-1,1):
        for role in (f'wheel_{side}',f'rim_hollow_{side}',f'wheel_web_{side}',f'hub_{side}'):
            a[role]['frame_mm'][2][3]-=.20
        for i in range(8):
            for end in ('start','end'):a[f'spoke_{side}_{i}'][end][2]-=.20
    for end in ('start','end'):a['axle'][end][2]-=.20
    p['underbody'].update(front_edge_y_mm=.45,rear_edge_y_mm=6.5,upper_length_mm=6.05,
        unclipped_upper_width_mm=6.7,face_angle_from_vertical_degrees=math.degrees(math.atan(1.85/2.52)))
    p['wheel_ground_burial_mm']=.20
    return finish(data,'chariot',seed,'Full floor perimeter is backed by the clipped taper; front board and rear deck lip included. Wheel contact patches and axle are lowered 0.20 mm into the base.')


def driver_coat_v3(seed):
    from .spearmen import cube
    data=driver_coat_v2(seed).to_dict();data['version']=3;p=data['parameters']
    removed={'belt_underside','coat_depth_clip'}
    p['atoms']=[a for a in p['atoms'] if a['role'] not in removed]
    p['operations']=[o for o in p['operations'] if o['target'] not in removed and o['operand'] not in removed]
    clip=dict(cube('coat_hip_clip',[0,-.02,-1.3],[2.16,1.42,1.6],0),export=False);p['atoms'].append(clip)
    for side in (-1,1):
        cone=square_taper(f'coat_hip_taper_{side}',[side*.51,0],-1.90,-.80,.38,1.48)
        p['atoms'].append(cone)
        p['operations'] += [dict(target=cone['role'],operand=clip['role'],operation='INTERSECT',solver='EXACT'),
                             dict(target='belt',operand=cone['role'],operation='UNION',solver='EXACT')]
        i=next(i for i,a in enumerate(p['atoms']) if a['role']==f'coat_tail_{side}')
        p['atoms'][i]=dict(long_shape(f'coat_tail_{side}',[side*.64,.4,-.6],[side*.80,.33,-1.48],1.0,.55),export=True)
    return finish(data,'chariot-driver-coat',seed,'Separate lower-coat tapers begin inside each hip and merge under the belt. Shorter split tails overlap these tapers instead of starting in midair.')


def horse_v3(seed):
    data=horse_v2(seed).to_dict();data['version']=3;p=data['parameters']
    solids={o['operand'] for o in p['operations'] if o['target']=='barrel' and o['operation']=='UNION'}
    for atom in p['atoms']:
        if atom['role'] in solids and atom['primitive']=='cone' and not atom['role'].endswith('_hoof'):
            atom['radius1']+=.02;atom['radius2']+=.02
    p['tangent_frustum_overlap_mm']=.024
    return finish(data,'chariot-horse',seed,'Steeper hind hocks, planted endpoints and 0.024 mm overlap at rounded positive tangent joins. This covers the polygonal sampling gap without changing the anatomy landmarks.')


def belly_blends_v2(seed):
    data=belly_blends(seed).to_dict();data['version']=2
    for atom in _chain('grounded_tail',[([.55,3.0,.20],.40),([.42,3.28,1.10],.40),([.30,3.51,2.15],.38)]):
        atom['export']=True;data['parameters']['atoms'].append(atom)
    return finish(data,'chariot-horse-belly-blends',seed,'Inner chest and haunch stock supports the barrel. A broad curved tail continuation meets the base and supports the original hanging tip.')


def spear_v2(seed):
    data=spear(seed).to_dict();data['version']=2
    source=json.loads((Path(__file__).parent/'parts/aurelian.uniform-spear-140-trial@3.json').read_text(encoding='utf-8'))
    data['parameters']['decorative_blade']['source_sha256']=ComponentDefinition.from_dict(source).sha256
    return finish(data,'chariot-spear',seed,'Full terminal cap proven continuous in the first chariot slice; source provenance explicitly pins the locked revision 3 definition. Shaft and mounts unchanged.')


def mage_robe_v2(seed):
    from .spearmen import cube
    data=mage_robe(seed).to_dict();data['version']=2;p=data['parameters']
    stock=taper('book_pouch_underside',[-.70,-.36,-2.6],[-.95,-.87,-1.1],.22,.95,depth=.8,vertices=4)
    stock['frame_mm']=multiply(stock['frame_mm'],rotation([0,0,45]))
    clip=dict(cube('book_pouch_cap',[-.95,-.6,-2.55],[3,3,2.20],0),export=False)
    p['atoms'] += [stock,clip]
    p['operations'] += [dict(target=stock['role'],operand=clip['role'],operation='INTERSECT',solver='EXACT'),
                        dict(target='robe',operand=stock['role'],operation='UNION',solver='EXACT')]
    return finish(data,'chariot-mage-regalia',seed,'Deck-seated robe plus a tapered book pouch grown from the robe into the book underside. Book cover and clasp stay visible.')


def helmet(seed, general=False):
    from .spearmen import cube
    ref='aurelian.swordmaster-sergeant-helmet-accepted-r2@5' if general else 'aurelian.readable-helmet-trial@5'
    data=json.loads((Path(__file__).parent/'parts'/f'{ref}.json').read_text(encoding='utf-8'))
    data['version']=1;p=data['parameters']
    if general:
        common=json.loads((Path(__file__).parent/'parts/aurelian.readable-helmet-trial@5.json').read_text(encoding='utf-8'))['parameters']
        atoms={a['role']:a for a in common['atoms']}
        for role in ('nape_ellipsoid','nape_limits','nape_front_clearance'):p['atoms'].append(deepcopy(atoms[role]))
        p['operations'][1:1]=[
            dict(target='nape_ellipsoid',operand='nape_limits',operation='INTERSECT',solver='EXACT'),
            dict(target='helmet_crown',operand='nape_ellipsoid',operation='UNION',solver='EXACT')]
        p['operations'].append(dict(target='helmet_crown',operand='nape_front_clearance',operation='DIFFERENCE',solver='EXACT'))
    # Clip the existing face-window operand with two roof planes. The aperture
    # keeps its full width through the eyes; its ceiling narrows to a short cap.
    roof=[]
    for side in (-1,1):
        angle=side*math.degrees(math.atan(.5));normal=[math.sin(math.radians(angle)),0,math.cos(math.radians(angle))]
        frame=multiply(translation([-4*normal[0],0,.85-4*normal[2]]),rotation([0,angle,0]))
        atom=dict(cube(f'face_roof_clip_{side}',[0,0,0],[8,8,8],0),frame_mm=frame,export=False)
        p['atoms'].append(atom)
        roof.append(dict(target='helmet_face_opening',operand=atom['role'],operation='INTERSECT',solver='EXACT'))
    p['operations'][0:0]=roof
    p['face_window_roof']=dict(apex_z_mm=.85,slope=.5,existing_center_ceiling_z_mm=.8,
                               full_width_through_z_mm=.515,flat_cap_width_mm=.20)
    p['source_reference']=ref
    return finish(data,'chariot-general-helmet' if general else 'chariot-helmet',seed,
                  'Outer crown, pointed top and head mount unchanged. Sloping face-window ceiling replaces the broad flat ledge; eye centers and nose remain clear. General also receives the approved lower nape profile.')


def general_helmet_v2(seed):
    from .spearmen import cube
    data=helmet(seed,True).to_dict();data['version']=2;p=data['parameters']
    brow=next(a for a in p['atoms'] if a['role']=='reinforced_brow')
    brow['location'][2]=.755;brow['dimensions'][2]=.41
    angle=math.degrees(math.atan(.625));normal=[0,math.sin(math.radians(angle)),math.cos(math.radians(angle))]
    anchor=[0,-.60,.56];center=[anchor[i]+4*normal[i] for i in range(3)]
    clip=dict(cube('brow_underside_clip',[0,0,0],[8,8,8],0),
              frame_mm=multiply(translation(center),rotation([-angle,0,0])),export=False)
    p['atoms'].append(clip)
    index=next(i for i,o in enumerate(p['operations']) if o['operand']=='reinforced_brow')
    p['operations'].insert(index,dict(target='reinforced_brow',operand=clip['role'],operation='INTERSECT',solver='EXACT'))
    p['brow_underside']=dict(rear_y_mm=-.6,rear_z_mm=.56,front_y_mm=-1.0,front_z_mm=.81,upper_z_mm=.96)
    return finish(data,'chariot-general-helmet',seed,'Supported nape and sloped face-window ceiling, with a rising underside beneath the raised command brow. Outer crown and pointed top remain pinned.')


def all_parts(seed):
    return [chassis(seed),driver_coat(seed),mage_robe(seed),command_sword(seed),spear(seed),horse(seed),
            *[arms(kind,seed) for kind in ('spear','driver','general','hero','mage')],chassis_v4(seed),driver_coat_v2(seed),horse_v2(seed),belly_blends(seed),chassis_v5(seed),driver_coat_v3(seed),horse_v3(seed),belly_blends_v2(seed),spear_v2(seed),mage_robe_v2(seed),helmet(seed),helmet(seed,True),general_helmet_v2(seed)]
