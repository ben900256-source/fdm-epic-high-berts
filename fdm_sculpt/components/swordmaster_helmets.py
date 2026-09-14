"""Forged officer helmet retaining the approved swordmaster crown."""
import math
from .spearmen import cube
from .core import ComponentDefinition
from .parts import validate_part
from .swordmaster_armour import waist_armour
from .spearmen import sphere,link


def officer_helmet(parent,seed):
    if type(seed) is not int:raise ValueError('explicit integer seed required')
    if parent.reference!='aurelian.helmet@5':raise ValueError('approved crown required')
    data=parent.to_dict()
    data.update(component_id='aurelian.swordmaster-sergeant-helmet',version=1,name='Swordmaster officer forged plate helmet')
    p=data['parameters'];atoms=[cube('reinforced_brow',[0,-.8,.7],[1.55,.4,.25],.045)]
    for side in (-1,1):
        tag='left' if side<0 else 'right'
        atoms.extend([cube(tag+'_temple_plate',[side*.73,0,.77],[.38,1.25,1.15],.09),
            cube(tag+'_raised_panel',[side*.91,-.02,.83],[.15,.85,.75],.035)])
    atoms.append(dict(role='officer_brow_badge',primitive='cone',export=False,location=[0,-1.01,.81],
        radius1=.29,radius2=.23,depth=.18,vertices=4,rotation=[math.pi/2,0,0],bevel=.025))
    p['atoms'].extend(atoms)
    p['operations'].extend(dict(target='helmet_crown',operand=a['role'],operation='UNION',solver='EXACT') for a in atoms)
    p.update(seed=seed,parent_reference=parent.reference,parent_definition_sha256=parent.sha256,
        provenance='Original forged temple plates, raised panels and reinforced brow; approved crown and face opening retained. Visual-only.')
    return validate_part(ComponentDefinition.from_dict(data))


def officer_waist(seed):
    data=waist_armour(seed).to_dict()
    data.update(component_id='aurelian.swordmaster-sergeant-waist',version=1,name='Swordmaster officer engraved waist armor')
    p=data['parameters']
    for a in p['atoms']:
        if a['role']=='central_plate':a.update(location=[0,-1.07,-1.87],dimensions=[1.38,.58,2.04])
        elif a['role']=='belt_jewel':a['dimensions']=[.88,.4,.68]
    atoms=[]
    for side in (-1,1):
        atoms.extend([cube(f'layered_plate_{side}',[side*.91,-1.01,-1.78],[.66,.27,1.15],.10),
            link(f'chevron_upper_{side}',[side*.47,-1.37,-1.32],[0,-1.42,-1.73],.115),
            link(f'chevron_lower_{side}',[side*.40,-1.37,-1.79],[0,-1.42,-2.20],.105),
            sphere(f'belt_stud_{side}',[side*.55,-1.16,-.88],[.23,.22,.23])])
    atoms.append(dict(role='officer_waist_badge',primitive='cone',export=False,location=[0,-1.43,-1.09],
        radius1=.32,radius2=.26,depth=.2,vertices=4,rotation=[math.pi/2,0,0],bevel=.025))
    p['atoms'].extend(atoms)
    p['operations'].extend(dict(target='belt',operand=a['role'],operation='UNION',solver='EXACT') for a in atoms)
    cutter=cube('engraved_center',[0,-1.43,-2.4],[.12,.16,.46],.03)
    p['atoms'].append(cutter);p['operations'].append(dict(target='belt',operand=cutter['role'],operation='DIFFERENCE',solver='EXACT'))
    return validate_part(ComponentDefinition.from_dict(data))


def oval_gem_helmet(parent,seed):
    data=officer_helmet(parent,seed).to_dict()
    data.update(version=2,name='Swordmaster officer helmet with seated oval brow gem')
    p=data['parameters']
    p['atoms']=[a for a in p['atoms'] if a['role']!='officer_brow_badge']
    p['operations']=[o for o in p['operations'] if o['operand']!='officer_brow_badge']
    atoms=[sphere('gem_setting',[0,-.7,1.02],[.58,.6,.68]),
           sphere('oval_brow_gem',[0,-.95,1.02],[.38,.22,.5])]
    p['atoms'].extend(atoms)
    p['operations'].extend(dict(target='helmet_crown',operand=a['role'],operation='UNION',solver='EXACT') for a in atoms)
    p['landmarks']['brow_gem']=[0,-.95,1.02]
    p['provenance']='Forged officer helmet with oval gem raised into a crown-backed setting above the brow. Visual-only.'
    return validate_part(ComponentDefinition.from_dict(data))
