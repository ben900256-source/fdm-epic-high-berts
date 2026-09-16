"""Visual sole projection and contact on the cached boots.

Run in background Blender with an atelier review directory. This is a visual
fit probe, not a manufacturing, manifold, overhang or sliced-detail check.
"""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

output=Path(sys.argv[-1])
job=json.loads((output/'assembly-job.json').read_text())
placements={p['instance_id']:p for p in job['assembly']['placements']}
loaded={}


def geometry(p, role=None):
    ref=p['part']
    if ref not in loaded:
        directory=Path(job['assets'][ref]['directory'])
        record=json.loads((directory/'asset.json').read_text())
        with bpy.data.libraries.load(str(directory/'part.blend'),link=True) as (_,request):
            request.collections=[record['visual_collection']]
        loaded[ref]=request.collections[0]
    vertices=[]
    faces=[]
    for obj in loaded[ref].objects:
        if role and not role(obj['component_geometry_role']):
            continue
        offset=len(vertices)
        matrix=Matrix(p['mount'])@obj.matrix_basis
        vertices.extend(matrix@v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in f.vertices] for f in obj.data.polygons)
    return vertices,BVHTree.FromPolygons(vertices,faces)


def touches(left,right):
    lv,lt=left
    rv,rt=right
    if lt.overlap(rt):
        return True
    # A wholly embedded wrist/shoulder need not intersect the outer surface.
    for points,tree in ((lv,rt),(rv,lt)):
        for vertex in points:
            nearest,normal,_,distance=tree.find_nearest(vertex)
            if nearest is not None and ((vertex-nearest).dot(normal)<-1e-5 or distance<1e-5):
                return True
    return False



checks=[]
for name,p in placements.items():
 params=job['assets'][p['part']]['definition']['parameters']
 if 'sole_fit' not in params:continue
 a=next(a for a in params['atoms'] if a['role'].endswith('_sole'))
 side=a['role'].split('_')[0]
 sole=geometry(p,lambda role:role==side+'_sole')
 toe=geometry(p,lambda role:role==side+'_toe')
 inverse=(Matrix(p['mount'])@Matrix(a['frame_mm'])).inverted()
 front=lambda vertices:min((inverse@v).y for v in vertices)
 checks.append(dict(instance=name,projection_mm=front(toe[0])-front(sole[0]),toe_contact=touches(sole,toe)))
report=dict(label='Visual boot fit only; not print validation',checks=checks,passes=bool(checks) and all(-.001<c['projection_mm']<.05 and c['toe_contact'] for c in checks))
(output/'sole-fit-contact.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
assert report['passes']
