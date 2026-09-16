"""Visual contact between aligned hands, sleeves and held items.

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



manifest=json.loads(Path('specs/hand-alignment-sources.json').read_text())
records={r['source'].split('@')[0]+'@'+str(r['version']):r for r in manifest['parts']}
checks=[]
for name,p in placements.items():
 if p['part'] not in records: continue
 record=records[p['part']]
 prefix=name.rsplit('/',1)[0]+'/' if '/' in name else ''
 item=placements[prefix+record['item_slot']]
 hand=geometry(p,lambda role:any(k in role for k in ('palm','fingers','thumb','knuckle_plate','falconry_glove')))
 sleeve=geometry(p,lambda role:role=='robe_sleeve')
 checks.append(dict(instance=name,part=p['part'],item=item['part'],wrist_contact=touches(hand,sleeve),item_contact=touches(hand,geometry(item))))
report=dict(label='Visual grip contact only; not manufacturing validation',checks=checks,passes=bool(checks) and all(c['wrist_contact'] and c['item_contact'] for c in checks))
(output/'hand-alignment-contact.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
assert report['passes']
