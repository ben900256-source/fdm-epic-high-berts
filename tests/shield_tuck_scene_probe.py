"""Visual contact checks for tucked shields, their grips and concealed hem joins.

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
 if not name.endswith('/shield'): continue
 prefix=name.rsplit('/',1)[0]+'/'
 skirt=geometry(placements[prefix+'skirt'])
 shield=geometry(p)
 # The forward shield face must never be crossed by the decorative trim.
 # Intentional contact at the rear remains separate from this visual check.
 shield_inverse=Matrix(p['mount']).inverted()
 front_vertices=[]
 front_faces=[]
 for obj in loaded[p['part']].objects:
  matrix=Matrix(p['mount'])@obj.matrix_basis
  for face in obj.data.polygons:
   verts=[matrix@obj.data.vertices[i].co for i in face.vertices]
   if all((shield_inverse@v).y < -.519 for v in verts):
    n=len(front_vertices)
    front_vertices.extend(verts)
    front_faces.append(list(range(n,n+len(verts))))
 trim=geometry(placements[prefix+'skirt-trim'])
 trim_inverse=Matrix(placements[prefix+'skirt-trim']['mount']).inverted()
 trim_x=[(trim_inverse@v).x for v in trim[0]]
 assert max(trim_x)-min(trim_x)>3.9, 'Recess must preserve the surrounding hem band'
 front_crossings=len(BVHTree.FromPolygons(front_vertices,front_faces).overlap(trim[1]))
 join=geometry(placements[prefix+'shield-lower-connector'])
 hand=geometry(placements[prefix+'left-arm'],lambda r: any(k in r for k in ('palm','fingers','thumb')))
 torso_join=geometry(placements[prefix+'shield-torso-connector'])
 low=min(v.z for v in shield[0])
 shield_inverse=Matrix(p['mount']).inverted()
 inset=min((shield_inverse@v).y for v in join[0])-min((shield_inverse@v).y for v in shield[0])
 local_bottom=min((shield_inverse@v).z for v in shield[0])
 bottom_offsets=[]
 for v in shield[0]:
  if (shield_inverse@v).z>local_bottom+1e-5: continue
  q,n,_,dist=join[1].find_nearest(v)
  bottom_offsets.append((v-q).dot(n))
 offsets=[]
 for v in shield[0]:
  # The backing is deliberately recessed from the face. Check the rear of
  # the lower tip remains embedded, and independently check front clearance.
  if v.z>low+.10 or (shield_inverse@v).y<0: continue
  q,n,_,dist=join[1].find_nearest(v)
  offsets.append((v-q).dot(n))
 c=dict(figure=prefix, trim_front_crossings=front_crossings, shield_join=touches(shield,join),skirt_join=touches(skirt,join),hand=touches(shield,hand),torso_join=touches(shield,torso_join),front_inset_mm=inset,rear_tip_to_join_max_offset=max(offsets),bottom_edge_to_join_max_offset=max(bottom_offsets))
 checks.append(c)
report=dict(label='Visual fit only; no slicing or manufacturing validation',checks=checks)
(output/'shield-tuck-contact.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
assert checks and all(all(c[k] for k in ('shield_join','skirt_join','hand','torso_join')) and c['rear_tip_to_join_max_offset'] < 0 and c['bottom_edge_to_join_max_offset'] < 0 and c['front_inset_mm'] > .08 and c['trim_front_crossings'] == 0 for c in checks)
