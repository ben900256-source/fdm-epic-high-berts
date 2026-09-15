"""Blender-free, pinned adaptations for the first modular infantry trial."""
import math
import copy

from .core import ComponentDefinition
from .parts import catalog, validate_part


def trial_equipment_brace(definitions=None, *, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    definitions = catalog() if definitions is None else definitions
    original = definitions['aurelian.equipment-joins@2']
    data = original.to_dict()
    data.update(version=3, name='Print trial spear brace with increased overlap')
    data['parameters']['atoms'][0]['radius'] = .405
    data['parameters'].update(seed=seed, source_definition_sha256=original.sha256,
                              design='Increase brace diameter by 0.01 mm; preserve endpoints and equipment placement.')
    return validate_part(ComponentDefinition.from_dict(data))


def trial_mail_skirt(definitions=None, *, seed):
    if type(seed) is not int:
        raise ValueError('an explicit integer seed is required')
    definitions = catalog() if definitions is None else definitions
    original = definitions['aurelian.skirt@3']
    data = original.to_dict()
    data.update(version=4, name='Trial chainmail skirt with coarse open recesses')
    parameters = data['parameters']
    backing = next(a for a in parameters['atoms'] if a['role'] == 'mail_skirt_backing')
    atoms, operations = [backing], []
    for row in range(8):
        z = -4.50 + row*.51
        radius = 1.55 + (.97-1.55)*((z+4.85)/4.35)
        count = max(8, round(2*math.pi*radius*.87/.72))
        for index in range(count):
            angle = 2*math.pi*(index+.5*(row%2))/count
            nx, ny = math.cos(angle), math.sin(angle)/.75
            length = math.hypot(nx, ny)
            nx, ny = nx/length, ny/length
            frame = [[ny,nx,0,radius*math.cos(angle)+.07*nx],
                     [-nx,ny,0,.75*radius*math.sin(angle)+.07*ny],
                     [0,0,1,z],[0,0,0,1]]
            role = f'trial_link_{row}_{index}'
            atoms.append(dict(role=role, primitive='sphere', export=True,
                              dimensions=[.70,.42,.65], location=[0,0,0], frame_mm=frame,
                              segments=16, ring_count=12))
            atoms.append(dict(role=role+'_eye', primitive='sphere', export=False,
                              dimensions=[.22,.40,.24], location=[0,.30,0], frame_mm=frame,
                              segments=16, ring_count=12))
            operations.append(dict(target=role, operand=role+'_eye', operation='DIFFERENCE', solver='EXACT'))
    parameters.update(atoms=atoms, operations=operations, seed=seed,
                      print_trial=dict(source=original.reference, source_sha256=original.sha256,
                                       relief_mm=.28, recess_depth_mm=.11,
                                       recess_stops_outside_backing_mm=.17))
    data['output_roles'] = [a['role'] for a in atoms if a['export']]
    return validate_part(ComponentDefinition.from_dict(data))


def spaced_trial_mail_skirt(definitions=None, *, seed):
    prior = trial_mail_skirt(definitions, seed=seed)
    data = prior.to_dict()
    data.update(version=5, name='Trial chainmail with separated links above the hem')
    parameters = data['parameters']
    backing, outer, eye = parameters['atoms'][:3]
    atoms, operations = [backing], []
    for row in range(6):
        z = -4.15 + row*.65
        radius = 1.55 + (.97-1.55)*((z+4.85)/4.35)
        count = max(5, math.floor(2*math.pi*radius*.75/.85))
        for index in range(count):
            angle = 2*math.pi*(index+.5*(row%2))/count
            nx, ny = math.cos(angle), math.sin(angle)/.75
            length = math.hypot(nx,ny)
            nx, ny = nx/length, ny/length
            frame = [[ny,nx,0,radius*math.cos(angle)+.07*nx],
                     [-nx,ny,0,.75*radius*math.sin(angle)+.07*ny],
                     [0,0,1,z],[0,0,0,1]]
            role = f'trial_link_{row}_{index}'
            raised, recess = copy.deepcopy(outer), copy.deepcopy(eye)
            raised.update(role=role, dimensions=[.65,.42,.55], frame_mm=frame)
            recess.update(role=role+'_eye', frame_mm=frame)
            atoms.extend([raised,recess])
            operations.append(dict(target=role,operand=role+'_eye',operation='DIFFERENCE',solver='EXACT'))
    parameters.update(atoms=atoms,operations=operations)
    parameters['print_trial'].update(supersedes_trial=prior.reference,
                                     vertical_link_gap_mm=.10, lowest_relief_z_mm=-4.425)
    data['output_roles'] = [a['role'] for a in atoms if a['export']]
    return validate_part(ComponentDefinition.from_dict(data))
