"""Original, Blender-free rectangular base and terrain recipes (visual only)."""
import argparse
import itertools
import json
import math
from pathlib import Path
import random

from .core import ComponentDefinition
from .elves_v2 import identity, multiply
from .parts import inverse_rigid, validate_part


def positive(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError(name+' must be finite and positive')
    return value


def definition(component_id, revision, family, atoms, operations, settings):
    return validate_part(ComponentDefinition.from_dict(dict(
        component_id=component_id, version=revision, name=component_id,
        family=family, required_anchors=['mount'], semantic_slots=['mono'],
        output_roles=[atoms[0]['role']], parameters=dict(atoms=atoms,
        operations=operations, landmarks={'mount':[0,0,0]}, recipe=settings))))


def cube(role, dimensions, location, export=False):
    return dict(role=role, primitive='cube', dimensions=dimensions,
                location=location, bevel=0, export=export)


def operation(target, operand, kind):
    return dict(target=target, operand=operand, operation=kind, solver='EXACT')


def base_body(component_id, revision, *, width=4, length=5, thickness=2,
              magnet='2x1', centers=None):
    for name, value in [('width',width),('length',length),('thickness',thickness)]:
        positive(value,name)
    if magnet not in ('none','2x1','3x1'):
        raise ValueError('magnet must be none, 2x1 or 3x1')
    centers = ([] if magnet=='none' else [[0,0]]) if centers is None else centers
    if magnet=='none' and centers:
        raise ValueError('nonmagnetic body cannot have pocket centers')
    radius = (int(magnet[0])+.2)/2 if magnet!='none' else 0
    depth = 1.1
    if thickness < .75 or (centers and thickness-depth < .75):
        raise ValueError('less than 0.75 mm roof stock')
    for i, center in enumerate(centers):
        if len(center)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in center):
            raise ValueError('pocket centers must be finite XY pairs')
        x,y = center
        if min(width/2-abs(x)-radius,length/2-abs(y)-radius)<.75:
            raise ValueError('less than 0.75 mm surrounding stock')
        for other in centers[:i]:
            if math.dist(center,other)-2*radius<.75:
                raise ValueError('less than 0.75 mm between pockets')
    atoms = [cube('body',[width,length,thickness],[0,0,thickness/2],True)]
    ops = []
    for i,(x,y) in enumerate(centers):
        role = f'magnet_{i}'
        # Extend cutter below zero; upper face is exactly 1.1 mm.
        atoms.append(dict(role=role,primitive='cylinder',radius=radius,depth=depth+.1,
                          location=[x,y,(depth-.1)/2],vertices=64,bevel=0,export=False))
        ops.append(operation('body',role,'DIFFERENCE'))
    return definition(component_id,revision,'base-body',atoms,ops,dict(
        width=width,length=length,thickness=thickness,magnet=magnet,centers=centers,
        diameter_allowance=.2,depth_allowance=.1,minimum_stock=.75,visual_only=True))


def boot_regions(placements, definitions, base_mount=None):
    """Conservative projected sole boxes in base coordinates; equipment is irrelevant."""
    inv = inverse_rigid(base_mount or identity())
    regions = []
    for p in placements:
        for atom in definitions[p['part']].to_dict()['parameters']['atoms']:
            if not atom['role'].endswith('_sole'):
                continue
            frame = multiply(multiply(inv,p['mount']),atom.get('frame_mm',identity()))
            corners = []
            for signs in itertools.product((-1,1),repeat=3):
                point = [atom['location'][i]+signs[i]*atom['dimensions'][i]/2 for i in range(3)]
                corners.append([sum(frame[i][j]*point[j] for j in range(3))+frame[i][3] for i in range(3)])
            regions.append([round(min(c[i] for c in corners)-.12,6) for i in range(2)]+
                           [round(max(c[i] for c in corners)+.12,6) for i in range(2)])
    return sorted(regions)


def _primitive_surface(component_id, revision, *, width=4, length=5, style='soil',
                    feature_scale=1, relief_height=.25, density=1, seed, boots=(), substrate_margin=.1):
    if type(seed) is not int:
        raise ValueError('seed must be an explicit integer')
    if type(substrate_margin) not in (int,float) or not math.isfinite(substrate_margin) or substrate_margin<0:
        raise ValueError('substrate margin must be finite and nonnegative')
    for name,value in [('width',width),('length',length),('feature_scale',feature_scale),
                       ('relief_height',relief_height),('density',density)]:
        positive(value,name)
    if style not in ('soil','sand','rocky','meadow'):
        raise ValueError('unknown terrain style')
    for box in boots:
        if len(box)!=4 or any(not math.isfinite(v) for v in box) or box[0]>=box[2] or box[1]>=box[3]:
            raise ValueError('invalid projected boot rectangle')
    rng = random.Random(seed)
    scale = feature_scale*(.52 if style=='sand' else 1)
    nx,ny = math.ceil(width/(scale*.7)*math.sqrt(density)),math.ceil(length/(scale*.7)*math.sqrt(density))
    if nx*ny>10000:
        raise ValueError('terrain exceeds 10000 features')
    # Avoid coplanar Exact intersection faces at the footprint and bottom.
    atoms = [cube('terrain',[width+2*substrate_margin,length+2*substrate_margin,.17+substrate_margin],
                  [0,0,-.065-substrate_margin/2],True)]
    ops = []
    def add(atom):
        atoms.append(atom)
        ops.append(operation('terrain',atom['role'],'UNION'))
    for i in range(nx):
        for j in range(ny):
            x = -width/2+(i+.5+rng.uniform(-.2,.2))*width/nx
            y = -length/2+(j+.5+rng.uniform(-.2,.2))*length/ny
            height = relief_height*rng.uniform(.45,1)*(.35 if style=='sand' else 1)
            add(dict(role=f'ground_{i}_{j}',primitive='sphere',export=False,
                     location=[x,y,(height-.12)/2],dimensions=[scale*rng.uniform(1.1,1.6),
                     scale*rng.uniform(1.1,1.6),height+.12],segments=16,ring_count=12))
    if style in ('rocky','meadow'):
        for i in range(max(1,round(width*length*density/5))):
            x,y = rng.uniform(-width/2,width/2),rng.uniform(-length/2,length/2)
            h = relief_height*rng.uniform(1.2,1.8)
            if style=='rocky':
                atom = cube(f'stone_{i}',[scale*1.1,scale*.8,h+.1],[x,y,(h-.1)/2])
                atom['bevel'] = min(.15,h/3,scale*.2)
                add(atom)
            else:
                for k in range(3):
                    add(dict(role=f'clump_{i}_{k}',primitive='sphere',export=False,
                             dimensions=[scale*.38,scale*.5,h+.1],
                             location=[x+(k-1)*scale*.2,y,(h-.1)/2],segments=16,ring_count=12))
    for i,(x0,y0,x1,y1) in enumerate(boots):
        role = f'boot_clearance_{i}'
        atoms.append(cube(role,[x1-x0,y1-y0,relief_height*4+1],
                          [(x0+x1)/2,(y0+y1)/2,.015+(relief_height*4+1)/2]))
        ops.append(operation('terrain',role,'DIFFERENCE'))
    atoms.append(cube('boundary',[width,length,relief_height*4+1],[0,0,(relief_height*4+1)/2-.15]))
    ops.append(operation('terrain','boundary','INTERSECT'))
    settings=dict(width=width,
        length=length,style=style,feature_scale=feature_scale,relief_height=relief_height,
        density=density,seed=seed,boots=list(boots),overlap=.15,visual_only=True)
    if substrate_margin:
        settings['substrate_margin']=substrate_margin
    return definition(component_id,revision,'terrain-surface',atoms,ops,settings)


def terrain_surface(component_id, revision, *, width=4, length=5, style='soil',
                    feature_scale=1, relief_height=.25, density=1, seed, boots=(),
                    method='heightfield', spacing=.065, substrate_margin=.1):
    if method=='primitives':
        return _primitive_surface(component_id,revision,width=width,length=length,style=style,
            feature_scale=feature_scale,relief_height=relief_height,density=density,seed=seed,
            boots=boots,substrate_margin=substrate_margin)
    if method!='heightfield':
        raise ValueError('unknown terrain method')
    if type(seed) is not int:
        raise ValueError('seed must be an explicit integer')
    for name,value in [('width',width),('length',length),('feature_scale',feature_scale),
                       ('relief_height',relief_height),('density',density)]:
        positive(value,name)
    if style not in ('soil','sand','rocky','meadow'):
        raise ValueError('unknown terrain style')
    for box in boots:
        if len(box)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in box) or box[0]>=box[2] or box[1]>=box[3]:
            raise ValueError('invalid projected boot rectangle')
    from .heightfield import sample_surface
    settings=dict(width=width,length=length,style=style,feature_scale=feature_scale,
                  relief_height=relief_height,density=density,seed=seed,boots=list(boots))
    grid=sample_surface(**settings,spacing=spacing)
    settings.update(method='heightfield',spacing=spacing,overlap=.15,visual_only=True,
                    technique='continuous layered noise and warped waves; original implementation')
    return definition(component_id,revision,'terrain-surface',
        [dict(role='terrain',primitive='heightfield',grid=grid,export=True)],[],settings)


def write_definition(part, directory):
    path = Path(directory)/(part.reference+'.json')
    if path.exists():
        if ComponentDefinition.from_dict(json.loads(path.read_text())).sha256 != part.sha256:
            raise ValueError('immutable revision exists; choose a new revision: '+part.reference)
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(part.to_dict(),indent=2)+'\n')
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=['body','surface'])
    parser.add_argument('component_id')
    parser.add_argument('--revision',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--width',type=float,default=4)
    parser.add_argument('--length',type=float,default=5)
    parser.add_argument('--thickness',type=float,default=2)
    parser.add_argument('--magnet',choices=['none','2x1','3x1'],default='2x1')
    parser.add_argument('--centers',type=json.loads,help='JSON array of XY pocket centers')
    parser.add_argument('--style',choices=['soil','sand','rocky','meadow'],default='soil')
    parser.add_argument('--feature-scale',type=float,default=1)
    parser.add_argument('--relief-height',type=float,default=.25)
    parser.add_argument('--density',type=float,default=1)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--boots',type=Path,help='JSON array of projected sole rectangles')
    args = parser.parse_args(argv)
    common = dict(width=args.width,length=args.length)
    if args.kind=='body':
        part = base_body(args.component_id,args.revision,**common,thickness=args.thickness,
                         magnet=args.magnet,centers=args.centers)
    else:
        part = terrain_surface(args.component_id,args.revision,**common,style=args.style,
            feature_scale=args.feature_scale,relief_height=args.relief_height,density=args.density,
            seed=args.seed,boots=json.loads(args.boots.read_text()) if args.boots else [])
    print(write_definition(part,args.output))


if __name__=='__main__':
    main()
