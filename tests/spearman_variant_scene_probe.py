"""Visual contact checks on cached soles, sword fists and the hawk perch."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fdm_sculpt.army import load_assembly
from fdm_sculpt.atelier import engine_hash
from fdm_sculpt.components.parts import catalog, cache_key

definitions = catalog()
objects = {}


def geometry(p):
    ref = p['part']
    if ref not in objects:
        d = definitions[ref]
        directory = ROOT/'out/part-cache'/cache_key(d, engine_hash(d))
        asset = json.loads((directory/'asset.json').read_text())
        with bpy.data.libraries.load(str(directory/'part.blend'), link=True) as (_, loaded):
            loaded.collections = [asset['visual_collection']]
        objects[ref] = list(loaded.collections[0].objects)
    return objects[ref]


def tree(p):
    vertices, faces = [], []
    for obj in geometry(p):
        offset = len(vertices)
        frame = Matrix(p['mount']) @ obj.matrix_basis
        vertices.extend(frame @ v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in face.vertices] for face in obj.data.polygons)
    return BVHTree.FromPolygons(vertices, faces)


def inside(t, point):
    hit, normal, _, distance = t.find_nearest(point)
    assert hit is not None and distance > .001
    assert (point-hit).dot(normal) < 0


soles, grips, feet = 0, 0, 0
for name in ('elf-spearman-variants', 'elf-spearman-hawk-sergeant'):
    a = load_assembly(ROOT/f'specs/{name}.json', definitions)
    slots = {p['instance_id']:p for p in a['placements']}
    for instance, p in slots.items():
        if instance.endswith(('/left-leg', '/right-leg')):
            for obj in geometry(p):
                if not obj.get('component_geometry_role', '').endswith('_sole'): continue
                m = Matrix(p['mount']) @ obj.matrix_basis
                heights = [(m @ v.co).z for v in obj.data.vertices]
                # Reviewed soles intentionally overlap the 2 mm body by .075 mm.
                assert abs(min(heights)-1.925) < .002 and max(heights) > 2.1, (instance, min(heights))
                soles += 1
        if instance.endswith('/shortblade'):
            center = Matrix(p['mount']) @ Vector((0,0,0))
            inside(tree(p), center)
            inside(tree(slots[instance.rsplit('/',1)[0]+'/right-arm']), center)
            grips += 1
        if instance.endswith('/hunting-hawk'):
            arm = tree(slots[instance.rsplit('/',1)[0]+'/left-arm'])
            hawk = tree(p)
            for x in (-.34, .34):
                center = Matrix(p['mount']) @ Vector((x,-.14,0))
                inside(arm, center)
                inside(hawk, center)
                feet += 1
assert soles == 22 and grips == 5 and feet == 4
report = dict(passes=True, grounded_soles=soles, held_swords=grips, perched_feet=feet)
(ROOT/'out/spearman-variant-contact-checks.json').write_text(json.dumps(report, indent=2)+'\n')
print('SPEARMAN_VISUAL_CONTACTS_VERIFIED', report)
