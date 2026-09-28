"""Visual clearance probe against cached meshes in an opened cavalry scene.

Run with Blender --background <assembly.blend> --python this-file.
This checks rein routing, not manufacturing printability.
"""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

source=bpy.data.objects['source/prince-01/reins']
definition=json.loads(source.instance_collection['definition_json'])
segments=[a for a in definition['parameters']['atoms'] if a['primitive']=='between']
mount=bpy.data.objects['prince-01/reins'].matrix_world
bit=mount@Vector(definition['parameters']['landmarks']['bit'])
grip=mount@Vector(definition['parameters']['landmarks']['grip'])

# Use the actual fist dimensions, including the rein radius at first contact.
# The former fixed centerline box rejected legitimate contact with the enlarged
# accepted fist before the center of the rein entered that smaller box.
hand=bpy.data.objects['prince-01/left-arm']
hand_source=bpy.data.objects['source/prince-01/left-arm']
hand_definition=json.loads(hand_source.instance_collection['definition_json'])
fist=next(a for a in hand_definition['parameters']['atoms'] if a['role']=='fist')
assert fist['primitive']=='cube' and 'rotation' not in fist and 'scale' not in fist
fist_frame=hand.matrix_world@Matrix(fist.get('frame_mm',Matrix.Identity(4)))
fist_inverse=fist_frame.inverted()
fist_half=Vector(fist['dimensions'])/2
fist_center=Vector(fist['location'])
grip_contacts=[]

def touches_fist_envelope(point,radius):
    delta=fist_inverse@point-fist_center
    distance=math.sqrt(sum(max(abs(delta[i])-fist_half[i],0)**2 for i in range(3)))
    return distance<=radius+.01

trees=[]
for instance in bpy.data.collections['VISUAL_PREVIEW'].objects:
    if instance.name.endswith('/reins'):continue
    for ob in instance.instance_collection.objects:
        matrix=instance.matrix_world@ob.matrix_basis
        tree=BVHTree.FromPolygons([matrix@v.co for v in ob.data.vertices],
                                 [list(p.vertices) for p in ob.data.polygons])
        trees.append((instance.name,tree))
bad=[];minimum={};contacts=[]
contact_segments=definition['parameters'].get('surface_contact_segments',[])
for i,segment in enumerate(segments):
    a,b=(mount@Vector(segment[key]) for key in ('start','end'))
    steps=math.ceil((b-a).length/.02)
    for j in range(steps+1):
        v=a.lerp(b,j/steps)
        for name,tree in trees:
            # Deliberate contacts at the bit and inside the fist only.
            if i==0 and (v-bit).length<.32 and name.endswith(('/horse','/barding')):continue
            if i==len(segments)-1 and name.endswith('/left-arm') and touches_fist_envelope(v,segment['radius']):
                grip_contacts.append(dict(segment=i,sample=j))
                continue
            loc,normal,index,distance=tree.find_nearest(v)
            direction=Vector((.873,.391,.291)).normalized();origin=v.copy();hits=0
            for _ in range(100):
                hit,_,_,_=tree.ray_cast(origin,direction)
                if hit is None:break
                hits+=1;origin=hit+direction*.0001
            signed=-distance if hits%2 else distance
            clearance=signed-segment['radius']
            minimum[name]=min(minimum.get(name,100),clearance)
            if i in contact_segments and name.endswith(('/horse','/barding')):
                if name.endswith('/horse'):contacts.append(signed)
                if signed>=-.055:continue  # Deliberate shallow surface relief.
            if clearance<.01:bad.append(dict(segment=i,sample=j,part=name,clearance=clearance))
result=dict(passes=not bad,component=definition['component_id'],revision=definition['version'],
            method='saved-mesh BVH distance and ray parity; 0.02 mm centerline samples, rein radius included',
            minimum_clearance_mm=minimum,collisions=bad,
            intended_grip_contact=dict(method='distance to saved fist primitive envelope, including rein radius',
                hand_component=hand_definition['component_id'],hand_revision=hand_definition['version'],
                fist_dimensions_mm=fist['dimensions'],samples=grip_contacts))
if contacts:
    result['body_contact_center_distance_mm']=[min(contacts),max(contacts)]
(Path(bpy.data.filepath).parent/'reins-clearance.json').write_text(json.dumps(result,indent=2)+'\n')
print('REINS_CLEARANCE',json.dumps(result))
assert result['passes'],bad[:10]
