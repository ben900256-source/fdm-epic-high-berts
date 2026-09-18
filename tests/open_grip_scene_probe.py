"""Visual fit/attachment probes on saved evaluated collections; no manufacturing audit.
Run Blender in the background with the assembled .blend and --python this file.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.grip_spears import clearance_profile, BOTTOM_Z, BED_AXIS_Z
from fdm_sculpt.components.parts import catalog, cache_key
from fdm_sculpt.atelier import engine_hash


def tree_of(vertices,faces):
    return BVHTree.FromPolygons(vertices,faces)


def clip_triangle(triangle,lo,hi):
    poly=list(triangle)
    for axis in range(3):
        for bound,sign in ((lo[axis],1),(hi[axis],-1)):
            result=[]
            for i,a in enumerate(poly):
                b=poly[(i+1)%len(poly)]
                da=sign*(a[axis]-bound); db=sign*(b[axis]-bound)
                if da>=0:result.append(a)
                if (da>=0)!=(db>=0):result.append(a+(b-a)*da/(da-db))
            poly=result
            if not poly:return False
    return len(poly)>=3


def islands(obj,matrix):
    mesh=obj.data
    parents=list(range(len(mesh.vertices)))
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    for edge in mesh.edges:
        a,b=edge.vertices;parents[find(a)]=find(b)
    groups=defaultdict(list)
    for face in mesh.polygons:groups[find(face.vertices[0])].append(tuple(face.vertices))
    vertices=[matrix@v.co for v in mesh.vertices]
    result=[]
    for faces in groups.values():
        ids=sorted({v for face in faces for v in face});remap={v:i for i,v in enumerate(ids)}
        verts=[vertices[i] for i in ids];polys=[tuple(remap[i] for i in face) for face in faces]
        result.append(dict(vertices=verts,tree=tree_of(verts,polys),lo=np.min(verts,axis=0),hi=np.max(verts,axis=0)))
    return result


def contained(tree,vertex):
    hit=tree.find_nearest(vertex)
    return hit[0] is not None and (vertex-hit[0]).dot(hit[1]) < -1e-5


def touching(a,b):
    if np.any(a['hi']<b['lo']-1e-5) or np.any(b['hi']<a['lo']-1e-5):return False
    if a['tree'].overlap(b['tree']):return True
    # No surface crossing: one connected shell can be enclosed by the other.
    return contained(a['tree'],b['vertices'][0]) or contained(b['tree'],a['vertices'][0])


def connected_groups(nodes):
    parents=list(range(len(nodes)))
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    for i,a in enumerate(nodes):
        for j in range(i):
            if find(i)!=find(j) and touching(a,nodes[j]):parents[find(i)]=find(j)
    groups=defaultdict(list)
    for i,node in enumerate(nodes):groups[find(i)].append(node['name'])
    return sorted(groups.values(),key=len,reverse=True)


def ray(tree,start,direction):
    hit=tree.ray_cast(Vector(start),Vector(direction),100)[0]
    if hit is None:raise AssertionError(('missing measurement surface',start,direction))
    return hit


def run():
    directory=Path(bpy.data.filepath).parent
    job=json.loads((directory/'assembly-job.json').read_text())
    placements=job['assembly']['placements'];assets=job['assets']
    meshes={};figures=defaultdict(list);hands=[];bounds_errors=[]
    definitions=catalog();source_collections={}
    assert not bpy.data.collections['EVALUATED_EXPORT'].objects
    for p in placements:
        instance=bpy.data.objects[p['instance_id']];objects=instance.instance_collection.objects
        for obj in objects:
            if not obj.data.polygons:continue
            mat=Matrix(p['mount'])@obj.matrix_basis
            mesh=obj.data;mesh.calc_loop_triangles()
            verts=np.array([mat@v.co for v in mesh.vertices])
            tris=verts[np.array([tuple(t.vertices) for t in mesh.loop_triangles])]
            role=obj['component_geometry_role'];name=p['instance_id']+'/'+role
            meshes[name]=tris
            if p['instance_id'].startswith('row-') and not p['instance_id'].endswith('/separate-spear'):
                for n,node in enumerate(islands(obj,mat)):
                    node['name']=name+f'#{n}';figures[p['instance_id'].split('/')[0]].append(node)
        definition=assets[p['part']]['definition'];params=definition['parameters']
        if 'centered_grip_clearance' in params:
            ref=params['centered_grip_clearance']['source']
            if ref not in source_collections:
                key=cache_key(definitions[ref],engine_hash(definitions[ref]))
                cache=ROOT/'out/part-cache'/key
                record=json.loads((cache/'asset.json').read_text())
                collection=bpy.data.collections.get(record['visual_collection'])
                if collection is None:
                    with bpy.data.libraries.load(str(cache/'part.blend'),link=True) as (_,loaded):
                        loaded.collections=[record['visual_collection']]
                    collection=loaded.collections[0]
                source_collections[ref]={o['component_geometry_role']:o for o in collection.objects}
            for obj in objects:
                if not obj.data.vertices:continue
                original=source_collections[ref][obj['component_geometry_role']]
                before=np.array([original.matrix_basis@v.co for v in original.data.vertices])
                after=np.array([obj.matrix_basis@v.co for v in obj.data.vertices])
                if np.any(after.min(0)<before.min(0)-.0001) or np.any(after.max(0)>before.max(0)+.0001):
                    bounds_errors.append(p['instance_id']+'/'+obj['component_geometry_role'])
        if 'open_grip_trial' not in params:continue
        info=params['open_grip_trial'];local=Matrix(info['grip_frame_mm']);cz=info['center_z_mm']
        palm=next(o for o in objects if o['component_geometry_role']=='right_palm')
        mat=local.inverted()@palm.matrix_basis
        palm_vertices=[mat@v.co for v in palm.data.vertices]
        tree=tree_of(palm_vertices,[tuple(f.vertices) for f in palm.data.polygons])
        raw_bounds=[]
        for atom in params['atoms']:
            if atom['role'] in ('right_palm','curled_thumb','finger_stock','thumb_stock') or atom['role'].startswith('curled_finger_'):
                center=np.array(atom['location']);half=np.array(atom['dimensions'])/2
                raw_bounds.extend((center-half,center+half))
            elif atom['role']=='palm_heel':
                for end in ('start','end'):
                    raw_bounds.extend((np.array(atom[end])-atom['radius'],np.array(atom[end])+atom['radius']))
        actual=np.array(palm_vertices)
        assert len(actual),f"Empty evaluated hand: {p['instance_id']}"
        within_bounds=bool(np.all(actual.min(0)>=np.min(raw_bounds,axis=0)-.0001) and
                           np.all(actual.max(0)<=np.max(raw_bounds,axis=0)+.0001))
        floor=ray(tree,(3,0,cz),(-1,0,0)).x
        rear=ray(tree,(-3,0,cz),(1,0,0)).x
        offsets=([info['underside']['full_depth_at_center_z_offset_mm']] if 'underside' in info
                 else [-.45+i*.3 for i in range(4)])
        lips=[ray(tree,(3,.78,cz+offset),(-1,0,0)).x for offset in offsets]
        # Across the second curled finger and the opposing thumb. The spaces
        # between rounded finger lobes deliberately widen the mouth locally.
        width_z=cz+(offsets[0] if 'underside' in info else -.15)
        width=ray(tree,(0,0,width_z),(0,1,0)).y-ray(tree,(0,0,width_z),(0,-1,0)).y
        roots=[]
        for offset in offsets:
            z=cz+offset
            roots.append(ray(tree,(-.399,3,z),(0,-1,0)).y-ray(tree,(-.399,0,z),(0,1,0)).y)
        center=Matrix(p['mount'])@Vector(params['landmarks']['grip_center'])
        spear=next(q for q in placements if q['instance_id']==p['instance_id'].replace('/right-arm','/separate-spear'))
        printed=Matrix(spear['mount']).inverted()@center
        hand_record=dict(instance=p['instance_id'],axis_error_mm=(printed.x**2+(printed.z-BED_AXIS_Z)**2)**.5,
            recess_depths_mm=[x-floor for x in lips],opening_width_mm=width,side_clearance_mm=(width-1)/2,
            recess_sample_offsets_mm=offsets,
            back_clearance_mm=-.3-floor,backing_stock_mm=floor-rear,finger_roots_mm=roots)
        sleeve=next(o for o in objects if o['component_geometry_role']=='robe_sleeve')
        palm_shells=islands(palm,palm.matrix_basis)
        sleeve_shells=islands(sleeve,sleeve.matrix_basis)
        hand_record['palm_shells']=len(palm_shells)
        hand_record['within_primitive_envelope']=within_bounds
        hand_record['attached_to_unchanged_sleeve']=all(
            any(touching(a,b) for b in sleeve_shells) for a in palm_shells)
        hands.append(hand_record)
        print('HAND',json.dumps(hand_record),flush=True)
    collisions=[]
    print_to_grip=Matrix(((0,0,1,-BED_AXIS_Z),(1,0,0,0),(0,1,0,BOTTOM_Z),(0,0,0,1)))
    for spear in (p for p in placements if p['instance_id'].endswith('/separate-spear')):
        frame=Matrix(spear['mount'])@print_to_grip.inverted();inv=np.array(frame.inverted())
        for name,world_tris in meshes.items():
            if name.startswith(spear['instance_id']+'/'):continue
            tri=world_tris@inv[:3,:3].T+inv[:3,3]
            for back,front,half,z0,z1 in clearance_profile():
                lo=np.array((back,-half,z0))+.0002;hi=np.array((front,half,z1))-.0002
                candidates=tri[((tri.max(1)>lo)&(tri.min(1)<hi)).all(1)]
                if any(clip_triangle(t,lo,hi) for t in candidates):
                    collisions.append(dict(spear=spear['instance_id'],part=name));break
    connectivity={}
    for figure,nodes in figures.items():
        groups=connected_groups(nodes)
        connectivity[figure]=dict(shells=len(nodes),groups=groups)
        print('CONTACTS',figure,len(nodes),'shells',len(groups),'connected groups',flush=True)
        if len(groups)>1:print('LOOSE',json.dumps(groups[1:]),flush=True)
    passed=(not collisions and not bounds_errors and all(h['axis_error_mm']<.05 and min(h['recess_depths_mm'])>=.64 and
        abs(h['opening_width_mm']-1.2)<.01 and abs(h['back_clearance_mm']-.1)<.01 and
        h['backing_stock_mm']>=.749 and min(h['finger_roots_mm'])>=.49 and
        h['palm_shells']==1 and h['attached_to_unchanged_sleeve'] and h['within_primitive_envelope'] for h in hands)
        and all(len(v['groups'])==1 for v in connectivity.values()))
    report=dict(mode='visual-only',hands=hands,full_insertion_path_collisions=collisions,
                difference_bounds_errors=bounds_errors,connectivity=connectivity,passed=passed)
    (directory/'grip-fit-probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print('COLLISIONS',json.dumps(collisions),flush=True)
    print('BOUNDS_ERRORS',json.dumps(bounds_errors),flush=True)
    assert passed,'Visual fit/attachment check failed; see grip-fit-probe.json'

if __name__=='__main__':run()
