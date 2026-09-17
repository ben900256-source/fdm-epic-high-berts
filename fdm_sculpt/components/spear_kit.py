"""Primitive-only flat spear and keyed socket experiments, revision 1."""
from math import pi, sqrt

from .core import ComponentDefinition
from .parts import validate_part

SEED = 1001
CLEARANCES = (0.15, 0.25, 0.35)  # total across-flat clearance, not per side


def cube(role, size, center, *, export=False, bevel=0, rotation=None):
    atom = dict(role=role, primitive='cube', dimensions=list(size), location=list(center),
                export=export, bevel=bevel)
    if rotation:
        atom['rotation'] = list(rotation)
    return atom


def operation(target, operand, kind='UNION'):
    return dict(target=target, operand=operand, operation=kind, solver='EXACT')


def definition(name, title, atoms, operations, **details):
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id='aurelian.'+name, version=1, name=title, family='spear-kit-trial',
        required_anchors=['mount'], semantic_slots=['mono'],
        output_roles=[a['role'] for a in atoms if a['export']],
        parameters=dict(atoms=atoms, operations=operations, landmarks={'mount':[0,0,0]},
                        seed=SEED, trial=details,
                        provenance='Flat sprue and keyed socket experiment. Physical fit and strength untested.'))))


def spear(width, upper=False):
    start, end = (2.0, 9.9) if upper else (0.0, 13.35)
    center = end + 0.65
    atoms = [cube('shaft', (width,end-start,0.8), (0,(start+end)/2,0.4), export=True, bevel=0.10)]
    operations = []
    if upper:
        atoms.append(cube('keyed_pin',(0.8,2.25,0.8),(0,1.125,0.4),bevel=0.08))
        operations.append(operation('shaft','keyed_pin'))
    # A clipped diamond prism prints with its full flat back against the bed.
    head_width = 1.8 if width == 1.0 else 2.0
    edge = head_width/sqrt(2)
    atoms.append(cube('head',(edge,edge,0.8),(0,center,0.4),export=True,
                      bevel=0.04,rotation=(0,0,pi/4)))
    cap_y = center + head_width/2 - 0.20
    atoms.append(cube('tip_clip',(10,10,10),(0,cap_y+5,0)))
    operations.append(operation('head','tip_clip','DIFFERENCE'))
    atoms.append(cube('socket_band',(width+0.3,0.65,0.8),(0,end-0.05,0.4),bevel=0.10))
    operations.append(operation('shaft','socket_band'))
    key = f'flat-spear-{"upper" if upper else "full"}-{round(width*100):03d}'
    return definition(key,f'Flat {"upper" if upper else "full"} spear, {width:.1f} x 0.8 mm',
                      atoms,operations,width_mm=width,thickness_mm=0.8,
                      kind='upper' if upper else 'full',pin_mm=[0.8,0.8,2.0] if upper else None,
                      cap_width_mm=0.4,length_mm=cap_y)


def frame():
    atoms=[cube('frame',(21,1,0.8),(7.5,-1,0.4),export=True)]
    operations=[]
    def add(atom):
        atoms.append(atom)
        operations.append(operation('frame',atom['role']))
    add(cube('top_rail',(21,1,0.8),(7.5,16.5,0.4)))
    for i,x in enumerate((-2.5,2.5,7.5,12.5,17.5)):
        add(cube(f'rail_{i}',(0.8,18.5,0.8),(x,7.75,0.4)))
    for i,(x,width,upper) in enumerate(((0,1,False),(5,1.2,False),(10,1,True),(15,1.2,True))):
        # Gates touch only the shaft, never the insertion pin or spearhead.
        for j,y in enumerate((1.2,10.8) if not upper else (3.1,8.0)):
            left=x-2.5
            end=x-width/2+0.18
            add(cube(f'clip_gate_{i}_{j}',(end-left,0.45,0.4),((end+left)/2,y,0.2)))
    add(cube('coupon_link',(1.5,3.5,0.8),(7.5,18,0.4)))
    return definition('flat-spear-sprue','Flat spear sprue with clip-off gates',atoms,operations,
                      gate_width_mm=0.45,gate_height_mm=0.4,
                      columns=['full-1.0','full-1.2','upper-1.0','upper-1.2'])


def coupon():
    atoms=[cube('coupon',(21,15.5,1),(7.5,26.75,0.5),export=True)]
    operations=[]
    records=[]
    for row,(width,kind) in enumerate(((1.0,'full-1.0'),(1.2,'full-1.2'),(0.8,'shared-upper-pin'))):
        y=21.5+5*row
        for column,clearance in enumerate(CLEARANCES):
            x=1.5+6*column
            name=f'socket_{row}_{column}'
            # Even the enlarged entry retains >=0.755 mm wall stock.
            atoms.append(cube(name,(3.3,3.3,2.65),(x,y,2.275)))
            operations.append(operation('coupon',name))
            hole=(width+clearance,0.8+clearance)
            cutter=name+'_hole'
            atoms.append(cube(cutter,(*hole,3.0),(x,y,2.7)))
            operations.append(operation('coupon',cutter,'DIFFERENCE'))
            # Shallow rectangular lead-in: larger top clearance, no interior roof.
            lead=name+'_lead'
            atoms.append(cube(lead,(hole[0]+0.24,hole[1]+0.24,0.30),(x,y,3.60)))
            operations.append(operation('coupon',lead,'DIFFERENCE'))
            records.append(dict(row=row+1,column=column+1,kind=kind,xy=[x,y],
                                opening_mm=list(hole),total_clearance_mm=clearance,
                                floor_z_mm=1.2,top_z_mm=3.6))
        # Raised tick marks identify rows 1/2/3; columns follow left to right.
        for tick in range(row+1):
            name=f'row_{row}_tick_{tick}'
            atoms.append(cube(name,(0.4,0.8,0.3),(-1.7+0.6*tick,y,1.15)))
            operations.append(operation('coupon',name))
    return definition('flat-spear-fit-coupon','Nine keyed fit sockets: 0.15 / 0.25 / 0.35 mm clearance',
                      atoms,operations,sockets=records,minimum_socket_wall_mm=0.755,
                      clearances_mm=list(CLEARANCES),socket_depth_mm=2.4)


def definitions(revision=1):
    parts=[spear(1.0),spear(1.2),spear(1.0,True),spear(1.2,True),frame(),coupon()]
    if revision == 2:
        for index in (2,3):
            data=parts[index].to_dict()
            data['version']=2
            data['name'] += ' with insertion stop'
            p=data['parameters']
            p['atoms'].append(cube('insertion_stop',(1.6,0.6,0.8),(0,2.3,0.4),bevel=0.05))
            p['operations'].append(operation('shaft','insertion_stop'))
            p['trial']['insertion_stop_width_mm']=1.6
            p['trial']['source']=parts[index].reference
            p['trial']['source_sha256']=parts[index].sha256
            parts[index]=validate_part(ComponentDefinition.from_dict(data))
    elif revision != 1:
        raise ValueError('Unknown trial revision')
    return parts


def assembly(parts,revision=1):
    placements=[]
    for index,part in enumerate(parts):
        x=5*index if index<4 else 0
        placements.append(dict(instance_id=f'kit/{part.component_id.split(".")[-1]}',
            part=part.reference,definition_sha256=part.sha256,
            mount=[[1,0,0,x],[0,1,0,0],[0,0,1,0],[0,0,0,1]]))
    return dict(schema_version=1,assembly_id=f'flat-spear-kit-v{revision}',
                label=f'Flat spear kit v{revision} — full shafts, upper sections and fit sockets',placements=placements)
