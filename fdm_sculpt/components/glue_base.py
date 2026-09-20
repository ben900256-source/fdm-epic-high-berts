"""Flat figure footings and a shared glue-in tray, in original recipe units."""
from copy import deepcopy

from .core import ComponentDefinition
from .elves_v2 import identity
from .parts import validate_part
from .terrain import cube, operation

SCALE = 1.3
TILE = (4.0, 5.0, 1.0)
COMPACT_PITCH_MM = 5.4
TRAY_MM = (28.7, 8.4, 2.0)
RECESS_MM = (27.1, 6.8, 1.2)
FLOOR_MM = .8


def definition(name, atoms, operations, revision=1, **recipe):
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id='aurelian.'+name, version=revision, name=name.replace('-', ' '),
        family='glue-base-trial', required_anchors=['mount'], semantic_slots=['mono'],
        output_roles=[a['role'] for a in atoms if a['export']],
        parameters=dict(atoms=atoms, operations=operations, landmarks={'mount':[0,0,0]},
                        seed=1001, recipe=recipe))))


def footing():
    return definition('glue-footing', [cube('footing', TILE, (0,0,.5), True)], [],
                      print_scale=SCALE, flat_printing_bottom=True)


def tray():
    width, depth, height = (v/SCALE for v in TRAY_MM)
    inner_x, inner_y, _ = (v/SCALE for v in RECESS_MM)
    floor = FLOOR_MM/SCALE
    atoms = [cube('tray', (width,depth,height), (0,0,height/2), True),
             cube('recess', (inner_x,inner_y,height-floor+.2),
                  (0,0,(height+floor+.2)/2))]
    return definition('glue-tray-five', atoms, [operation('tray','recess','DIFFERENCE')], revision=3,
                      print_scale=SCALE, outside_mm=TRAY_MM, recess_mm=RECESS_MM,
                      floor_mm=FLOOR_MM, wall_mm=.8, side_clearance_mm=.15,
                      pitch_mm=COMPACT_PITCH_MM,
                      seating='Five flat footings with 0.2 mm gaps in one shared recess',
                      physical_fit_tested=False)


def walled_tray():
    atoms=[cube('tray', (32.3/SCALE,8.4/SCALE,2/SCALE), (0,0,1/SCALE), True)]
    ops=[]
    for i in range(5):
        role=f'recess_{i+1}'
        atoms.append(cube(role,(5.5/SCALE,6.8/SCALE,1.4/SCALE),
                          ((i-2)*6.3/SCALE,0,1.5/SCALE)))
        ops.append(operation('tray',role,'DIFFERENCE'))
    return definition('glue-tray-five-walled',atoms,ops,print_scale=SCALE,
                      outside_mm=[32.3,8.4,2],recess_mm=[5.5,6.8,1.2],
                      floor_mm=.8,wall_mm=.8,side_clearance_mm=.15,
                      pitch_mm=6.3,physical_fit_tested=False)


def terrain_tile(source, index):
    data = deepcopy(source.to_dict())
    data.update(component_id=f'aurelian.glue-terrain-{index}', version=1,
                name=f'Terrain footing {index}')
    p = data['parameters']
    center = (index-3)*4
    p['atoms'].append(cube('footing_clip', (4,5,10), (center,0,0)))
    for role in data['output_roles']:
        p['operations'].append(operation(role,'footing_clip','INTERSECT'))
    p['glue_footing'] = dict(source=source.reference, source_sha256=source.sha256,
                            center_x=center, print_scale=SCALE)
    return validate_part(ComponentDefinition.from_dict(data))


def placement(name, part, x=0, y=0, z=0):
    mount=identity()
    for i,value in enumerate((x,y,z)):mount[i][3]=value
    return dict(instance_id=name, part=part.reference, definition_sha256=part.sha256, mount=mount)


def assemblies(source, definitions):
    ground = next(p for p in source['placements'] if p['instance_id']=='strip-terrain')
    tile, holder, walled = footing(), tray(), walled_tray()
    terrain = [terrain_tile(definitions[ground['part']], i) for i in range(1,6)]
    parts = [tile, holder, walled, *terrain]
    specs=[]
    assembled=[placement('tray', holder)]
    wide=[placement('tray',walled)]
    spread=[placement('tray', holder, x=-15,y=25),placement('walled-tray',walled,x=15,y=25)]
    for i, top in enumerate(terrain,1):
        prefix=f'row-{i:02}'
        center=(i-3)*4
        figures=[deepcopy(p) for p in source['placements'] if p['instance_id'].startswith(prefix+'/')]
        for p in figures:p['mount'][0][3]-=center
        items=[placement(prefix+'/footing',tile), placement(prefix+'/terrain',top,x=-center,z=1), *figures]
        specs.append(dict(schema_version=1,assembly_id=f'glue-figure-{i}-trial',
                          label=f'Glue-in figure {i} (source scale)',placements=items))
        for p in items:
            seated=deepcopy(p);seated['mount'][0][3]+=(i-3)*COMPACT_PITCH_MM/SCALE;seated['mount'][2][3]+=FLOOR_MM/SCALE
            assembled.append(seated)
            seated_wide=deepcopy(p);seated_wide['mount'][0][3]+=center
            seated_wide['mount'][2][3]+=FLOOR_MM/SCALE
            seated_wide['mount'][0][3]+=(i-3)*(6.3/SCALE-4)
            wide.append(seated_wide)
            separated=deepcopy(p);separated['mount'][0][3]+=(i-3)*18
            spread.append(separated)
    specs.extend([
        dict(schema_version=1,assembly_id='glue-base-assembled-trial',label='Glue-in row assembled (source scale)',placements=assembled),
        dict(schema_version=1,assembly_id='glue-base-walled-assembled-trial',label='Glue-in row with individual recesses (source scale)',placements=wide),
        dict(schema_version=1,assembly_id='glue-base-spaced-trial',label='Separate figures and glue-in tray (source scale)',placements=spread),
        dict(schema_version=1,assembly_id='glue-base-empty-trial',label='Empty glue-in tray (source scale)',placements=[placement('tray',holder)]),
        dict(schema_version=1,assembly_id='glue-base-walled-empty-trial',label='Empty tray with five recesses (source scale)',placements=[placement('tray',walled)])])
    return parts,specs
