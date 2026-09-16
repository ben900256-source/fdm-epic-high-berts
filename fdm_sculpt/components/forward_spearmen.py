"""Low spear poses with permanent deadwood rests; visual primitive recipes."""
from copy import deepcopy
import math

from .elves_v2 import identity, multiply, point, translation
from .parts import inverse_rigid
from .robe_arms import hand_atom
from .spearman_overhangs import finish, ramp
from .terrain import base_body, terrain_surface


def rotation_x(degrees):
    a=math.radians(degrees);c,s=math.cos(a),math.sin(a)
    return [[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]


def generate_parts(definitions, manifest, seed):
    if type(seed) is not int or seed!=manifest['seed']:
        raise ValueError('Use the pinned integer seed')
    for ref,sha in manifest['sources'].items():
        if definitions[ref].sha256!=sha:raise ValueError('Pinned source changed: '+ref)
    source=definitions[manifest['arm']]
    arm_mount=manifest['arm_mount'];old_spear=manifest['spear_mount']
    grip=point(old_spear,[0,.46,-.65])
    result=[base_body('aurelian.forward-base-extension',v,width=4,length=13.2,thickness=v,magnet='none') for v in (1,2)]
    result.append(terrain_surface('aurelian.forward-base-terrain',1,width=4,length=13.2,
                                 relief_height=.5,style='soil',seed=seed,spacing=.1))
    poses=[]
    for number,elevation in enumerate(range(0,46,5),1):
        rotation=rotation_x(90-elevation)
        spear_mount=multiply(translation(grip),multiply(rotation,translation([0,-.46,4.8])))
        old_rotation=[row[:3]+[0] for row in old_spear[:3]]+[[0,0,0,1]]
        hand_rotation=multiply(rotation,inverse_rigid(old_rotation))
        world=multiply(translation(grip),multiply(hand_rotation,translation([-x for x in grip])))
        local=multiply(inverse_rigid(arm_mount),multiply(world,arm_mount))
        data=deepcopy(source.to_dict());p=data['parameters']
        for atom in p['atoms']:
            if hand_atom(atom) or atom['role']=='fist_rising_envelope':
                atom['frame_mm']=multiply(local,atom.get('frame_mm',identity()))
        for name,value in list(p['landmarks'].items()):
            if hand_atom(dict(role=name)):p['landmarks'][name]=point(local,value)
        wrist=p['landmarks']['right_cuff'];palm=p['landmarks']['right_palm']
        bridge=ramp('forward_cloth_wrist',wrist,palm,.33,.32);bridge['export']=False
        p['atoms'].append(bridge)
        p['operations'].append(dict(target='robe_sleeve',operand=bridge['role'],operation='UNION',solver='EXACT'))
        p['forward_pose']=dict(seed=seed,elevation_degrees=elevation,source=source.reference,
                               source_sha256=source.sha256,hand_transform=local,grip_world=grip)
        p['provenance']+=' Hand rotated with the low spear; cloth wrist closes into the retained sleeve. Visual-only.'
        data.update(component_id=f'aurelian.forward-spear-arm-{number:02d}',version=1,
                    name=f'Forward spear hand, {elevation} degrees above horizontal')
        arm=finish(data);result.append(arm)
        atoms=[];contacts=[]
        # Three slender front rests and a short rear rest. Roots and forked
        # branches read as deadwood, and stay attached to the finished model.
        for index,distance in enumerate((-1.1,3.2,7.6,12.6)):
            shaft=point(spear_mount,[0,.46,-4.8+distance])
            underside=shaft[2]-(.51 if distance<12 else .60)*math.cos(math.radians(elevation))
            tip=[shaft[0],shaft[1],underside+.13]
            foot=[shaft[0]-.18,shaft[1]+.25,1.15]
            fork=[shaft[0]-.15,shaft[1]+.1,tip[2]-.8]
            if manifest.get('support_version',1)>=2:
                bend=[foot[0]-.14,foot[1]-.10,foot[2]+.48*(fork[2]-foot[2])]
                atoms.append(ramp(f'deadwood_stem_{index}',foot,bend,.42,.40))
                atoms.append(ramp(f'deadwood_stem_upper_{index}',bend,fork,.40,.39))
            else:
                atoms.append(ramp(f'deadwood_stem_{index}',foot,fork,.46,.39))
            atoms.append(ramp(f'spear_rest_{index}',fork,tip,.39,.375))
            if manifest.get('support_version',1)>=2:
                twig=[fork[0]-.85,fork[1]+.35,fork[2]+.65]
                atoms.append(ramp(f'deadwood_fork_{index}',
                                  [fork[0],fork[1],fork[2]-.60],twig,.375,.18))
                sprig=[fork[0]+.48,fork[1]+.32,fork[2]-.20]
                atoms.append(ramp(f'deadwood_sprig_{index}',
                                  [fork[0],fork[1],fork[2]-1.05],sprig,.32,.16))
            else:
                twig=[fork[0]-.30,fork[1]+.20,fork[2]+.45]
                atoms.append(ramp(f'deadwood_fork_{index}',
                                  [fork[0],fork[1],fork[2]-.45],twig,.375,.28))
            for root in (-1,1):
                atoms.append(ramp(f'deadwood_root_{index}_{root}',
                    [foot[0]+root*.43,foot[1]+.26,1.15],
                    [foot[0],foot[1],1.95],.39,.38))
            atoms.append(dict(role=f'root_stone_{index}',primitive='sphere',
                              location=[foot[0],foot[1],1.38],dimensions=[1.25,1.05,.65],
                              segments=12,ring_count=8,export=True))
            contacts.append(dict(distance_from_hand_mm=distance,shaft=shaft,tip=tip,foot=foot))
        support=finish(dict(component_id=f'aurelian.forward-spear-deadwood-{number:02d}',version=manifest.get('support_version',1),
            name=f'Permanent forked deadwood spear rests, {elevation} degrees',family='terrain-support',
            required_anchors=['mount'],semantic_slots=['mono'],parameters=dict(atoms=atoms,operations=[],
            landmarks={'mount':[0,0,0]},recipe=dict(seed=seed,elevation_degrees=elevation,
            permanent=True,contacts=contacts,minimum_stem_diameter_mm=.75,visual_only=True))))
        result.append(support)
        poses.append(dict(number=number,elevation=elevation,arm=arm.reference,
                          support=support.reference,spear_mount=spear_mount,
                          tip=point(spear_mount,[0,.46,8.75])))
    return result,poses
