"""Visual fit check: evaluated shoe surfaces must not cross the skirt trim."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

output = Path(sys.argv[-1])
job = json.loads((output/'assembly-job.json').read_text())
placements = {p['instance_id']:p for p in job['assembly']['placements']}
loaded = {}


def geometry(placement, roles=None):
    ref = placement['part']
    if ref not in loaded:
        asset = job['assets'][ref]
        record = json.loads((Path(asset['directory'])/'asset.json').read_text())
        with bpy.data.libraries.load(str(Path(asset['directory'])/'part.blend'),link=True) as (_, requested):
            requested.collections = [record['visual_collection']]
        loaded[ref] = requested.collections[0]
    vertices, faces = [], []
    for obj in loaded[ref].objects:
        if roles and obj.get('component_geometry_role') not in roles:
            continue
        offset = len(vertices)
        matrix = Matrix(placement['mount']) @ obj.matrix_basis
        vertices.extend(matrix@v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in p.vertices] for p in obj.data.polygons)
    assert vertices and faces
    return vertices, BVHTree.FromPolygons(vertices,faces)


checks = []
for name,p in placements.items():
    if '/left-leg' not in name and '/right-leg' not in name:
        continue
    prefix,slot = name.split('/')
    side = slot.split('-')[0]
    shoe, tree = geometry(p, {side+'_sole',side+'_toe'})
    trim_vertices, trim = geometry(placements[prefix+'/skirt-trim'])
    overlap = len(tree.overlap(trim))
    distance = min(min(trim.find_nearest(v)[3] for v in shoe),
                   min(tree.find_nearest(v)[3] for v in trim_vertices))
    checks.append(dict(instance=name, crossing_faces=overlap, sampled_clearance_mm=round(distance,6)))
report = dict(passes=all(c['crossing_faces']==0 and c['sampled_clearance_mm']>.025 for c in checks),
              label='Visual shoe/trim fit only; not a manufacturing validation', checks=checks)
(output/'shoe-trim-fit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
assert len(checks)==10 and report['passes'], 'shoe/trim fit failed'
