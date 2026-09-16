"""Visual sleeve-to-hand and sleeve-to-body contact in cached posed arms.

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
    if 'cloth_pose' not in params:
        continue
    sleeve=geometry(p,lambda role:role=='robe_sleeve')
    hand=geometry(p,lambda role:any(k in role for k in ('palm','falconry_glove','grouped_fingers','thumb')))
    prefix=name.rsplit('/',1)[0]+'/'
    body=[placements[prefix+slot] for slot in ('torso','tunic','mail') if prefix+slot in placements]
    hand_contact=touches(sleeve,hand)
    body_contact=any(touches(sleeve,geometry(b)) for b in body)
    checks.append(dict(instance=name,part=p['part'],hand_contact=hand_contact,
                       body_contact=body_contact,passes=hand_contact and body_contact))
report=dict(label='Visual cloth arm contact only; not manufacturing validation',
            checks=checks,passes=bool(checks) and all(c['passes'] for c in checks))
(output/'robe-arm-contact.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
assert report['passes']
