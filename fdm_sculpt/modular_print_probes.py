"""Read-only pocket, shaft and boot-contact measurements in a saved trial."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt.prusa import sha256


def tree_for(objects):
    vertices, polygons = [], []
    for obj, matrix in objects:
        offset = len(vertices)
        vertices.extend(matrix @ v.co for v in obj.data.vertices)
        polygons.extend(tuple(offset+i for i in p.vertices) for p in obj.data.polygons)
    return BVHTree.FromPolygons(vertices, polygons)


def run(output):
    output = Path(output)
    job = json.loads((output/'internal/assembly-job.json').read_text())
    master, = bpy.data.collections['EVALUATED_EXPORT'].objects
    tree = tree_for([(master, master.matrix_world)])
    records = []
    def diameters(radii):
        return [None if any(v is None for v in radii[i:i+2]) else sum(radii[i:i+2]) for i in (0,2)]
    for x in (-6,6):
        ceiling = tree.ray_cast(Vector((x,0,-.1)), Vector((0,0,1)))[0]
        top = None if ceiling is None else tree.ray_cast(Vector((x,0,ceiling.z+.00001)), Vector((0,0,1)))[0]
        radii = [tree.ray_cast(Vector((x,0,.55)), Vector(direction))[3]
                 for direction in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]]
        outer_sides = [tree.ray_cast(Vector((x,y,.55)), Vector((0,-1 if y>0 else 1,0)))[0] for y in (2.6,-2.6)]
        walls = [None if outer is None or radius is None else abs(outer.y)-radius
                 for outer,radius in zip(outer_sides,radii[2:])]
        stock = None if top is None or ceiling is None else top.z-ceiling.z
        records.append(dict(feature='magnet pocket', center_x_mm=x,
                            depth_mm=None if ceiling is None else ceiling.z,
                            diameters_mm=diameters(radii), side_walls_mm=walls, material_above_mm=stock,
                            passes=ceiling is not None and abs(ceiling.z-1.1)<.005 and
                                   all(r is not None and abs(r-1.6)<.005 for r in radii) and
                                   all(w is not None and w>=.75 for w in walls) and stock is not None and stock>=.75))
    for placement in job['assembly']['placements']:
        if placement['part'] != 'aurelian.spear@3':
            continue
        matrix = Matrix(placement['mount'])
        center = matrix @ Vector((0,.46,3.5))
        radii = [tree.ray_cast(center, matrix.to_3x3() @ Vector(d))[3]
                 for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]]
        widths = diameters(radii)
        records.append(dict(feature='spear shaft', instance_id=placement['instance_id'],
                            diameters_mm=widths, passes=all(w is not None and w>=1.0 for w in widths)))
    terrains = []
    for p in job['assembly']['placements']:
        if 'terrain-' in p['part'] or 'base-body-' in p['part']:
            collection = bpy.data.collections[job['assets'][p['part']]['manifest']['visual_collection']]
            terrains.extend((o, Matrix(p['mount']) @ o.matrix_basis) for o in collection.objects)
    ground = tree_for(terrains)
    for p in job['assembly']['placements']:
        if not p['instance_id'].endswith(('/left-leg','/right-leg')):
            continue
        collection = bpy.data.collections[job['assets'][p['part']]['manifest']['visual_collection']]
        points = []
        for obj in collection.objects:
            if not any(word in obj.get('component_geometry_role','') for word in ('sole','boot','toe')):
                continue
            matrix = Matrix(p['mount']) @ obj.matrix_basis
            points.extend(matrix @ v.co for v in obj.data.vertices)
        overlaps = 0
        for point in points:
            hit = ground.ray_cast(Vector((point.x,point.y,3)), Vector((0,0,-1)))[0]
            overlaps += hit is not None and point.z <= hit.z+.001
        records.append(dict(feature='boot/terrain overlap', instance_id=p['instance_id'],
                            contacting_vertices=overlaps, passes=overlaps>=3))
    result = dict(passes=all(r['passes'] for r in records), measurements=records,
                  stl_sha256=sha256(output/'elf-spearman-proof.stl'),
                  limitation='Selected geometric probes; complete structural qualification and a physical trial remain necessary')
    (output/'geometry-probes.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    run(sys.argv[sys.argv.index('--')+1])
