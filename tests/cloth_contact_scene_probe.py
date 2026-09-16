"""Check visible sleeve/arm contact and retained cape ground height."""
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


def geometry(p):
    ref=p['part']
    if ref not in loaded:
        directory=Path(job['assets'][ref]['directory'])
        record=json.loads((directory/'asset.json').read_text())
        with bpy.data.libraries.load(str(directory/'part.blend'),link=True) as (_, requested):
            requested.collections=[record['visual_collection']]
        loaded[ref]=requested.collections[0]
    vertices=[];faces=[]
    for obj in loaded[ref].objects:
        offset=len(vertices)
        matrix=Matrix(p['mount'])@obj.matrix_basis
        vertices.extend(matrix@v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in face.vertices] for face in obj.data.polygons)
    return vertices,BVHTree.FromPolygons(vertices,faces)


checks=[]
for name,p in placements.items():
    if name.endswith(('/left-tunic','/right-tunic')):
        _,sleeve=geometry(p)
        _,arm=geometry(placements[name.replace('-tunic','-arm')])
        count=len(sleeve.overlap(arm))
        checks.append(dict(instance=name,contact_faces=count,passes=count>0))
    elif name.endswith('/cape'):
        vertices,_=geometry(p)
        z=min(v.z for v in vertices)
        checks.append(dict(instance=name,ground_z=z,passes=abs(z-2)<1e-5))
report=dict(label='Visual contact only; not manufacturing validation',checks=checks,
            passes=len(checks)==15 and all(c['passes'] for c in checks))
(output/'cloth-contact.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
assert report['passes']
