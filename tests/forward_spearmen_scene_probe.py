"""Read-only visual contact checks; run with background Blender and a gallery."""
import bpy,json,sys
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

output=Path(sys.argv[-1]);job=json.loads((output/'assembly-job.json').read_text())
placements={p['instance_id']:p for p in job['assembly']['placements']};loaded={}


def geometry(p,role=None):
    ref=p['part']
    if ref not in loaded:
        folder=Path(job['assets'][ref]['directory']);record=json.loads((folder/'asset.json').read_text())
        with bpy.data.libraries.load(str(folder/'part.blend'),link=True) as (_,req):req.collections=[record['visual_collection']]
        loaded[ref]=req.collections[0]
    vertices=[];faces=[]
    for obj in loaded[ref].objects:
        if role and not role(obj['component_geometry_role']):continue
        offset=len(vertices);m=Matrix(p['mount'])@obj.matrix_basis
        vertices.extend(m@v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in f.vertices] for f in obj.data.polygons)
    return vertices,BVHTree.FromPolygons(vertices,faces)


def touches(a,b):
    if a[1].overlap(b[1]):return True
    for vertices,tree in ((a[0],b[1]),(b[0],a[1])):
        for v in vertices:
            hit,normal,_,distance=tree.find_nearest(v)
            if hit is not None and (distance<1e-5 or (v-hit).dot(normal)<-1e-5):return True
    return False


checks=[]
for n in range(1,11):
    prefix=f'forward-{n:02d}/'
    support=placements[prefix+'spear-terrain-rests'];spear=geometry(placements[prefix+'spear'])
    for index in range(4):
        rest=geometry(support,lambda r:r==f'spear_rest_{index}')
        roots=geometry(support,lambda r:r.startswith(f'deadwood_root_{index}_'))
        base=geometry(placements[f'base-{n:02d}' if index==0 else prefix+'forward-base-extension'])
        checks.append(dict(figure=n,rest=index,spear_contact=touches(rest,spear),base_contact=touches(roots,base)))
report=dict(label='Visual contact only; not printability validation',checks=checks,
            passes=all(c['spear_contact'] and c['base_contact'] for c in checks))
(output/'forward-spear-contacts.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
assert report['passes']
