"""Visual placement checks on the cached evaluated pieces, not print validation."""
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


def geometry(placement, roles=None, local=False):
    ref = placement['part']
    if ref not in loaded:
        directory = Path(job['assets'][ref]['directory'])
        record = json.loads((directory/'asset.json').read_text())
        with bpy.data.libraries.load(str(directory/'part.blend'), link=True) as (_, requested):
            requested.collections = [record['visual_collection']]
        loaded[ref] = requested.collections[0]
    vertices, faces = [], []
    for obj in loaded[ref].objects:
        if roles and obj.get('component_geometry_role') not in roles:
            continue
        offset = len(vertices)
        matrix = obj.matrix_basis if local else Matrix(placement['mount']) @ obj.matrix_basis
        vertices.extend(matrix @ v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in polygon.vertices] for polygon in obj.data.polygons)
    assert vertices and faces
    return vertices, BVHTree.FromPolygons(vertices, faces)


checks = []
for prefix in sorted({name.split('/')[0] for name in placements if name.endswith('/skirt')}):
    hem, _ = geometry(placements[prefix+'/skirt'], {'hem_ground_transition'})
    soles = []
    for side in ('left', 'right'):
        vertices, _ = geometry(placements[prefix+'/'+side+'-leg'], {side+'_sole'})
        soles.extend(vertices)
    trim, _ = geometry(placements[prefix+'/skirt-trim'], local=True)
    _, cape = geometry(placements[prefix+'/cape'], local=True)
    embedded = []
    for vertex in trim:
        near, normal, _, distance = cape.find_nearest(vertex)
        if distance > .005 and (vertex-near).dot(normal) < -.005:
            embedded.append(vertex)
    check = dict(figure=prefix, hem_bottom_mm=min(v.z for v in hem),
                 feet_bottom_mm=min(v.z for v in soles), trim_rear_mm=max(v.y for v in trim),
                 left_embedded_vertices=sum(v.x < 0 for v in embedded),
                 right_embedded_vertices=sum(v.x > 0 for v in embedded))
    check['passes'] = (check['hem_bottom_mm'] >= check['feet_bottom_mm'] and
                       check['trim_rear_mm'] > .5 and check['left_embedded_vertices'] > 0 and
                       check['right_embedded_vertices'] > 0)
    checks.append(check)
report = dict(label='Visual placement only; no manufacturing validation', checks=checks,
              passes=len(checks) == 5 and all(c['passes'] for c in checks))
(output/'hem-shoulder-fit.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report), flush=True)
assert report['passes'], 'visual hem/cape fit failed'
