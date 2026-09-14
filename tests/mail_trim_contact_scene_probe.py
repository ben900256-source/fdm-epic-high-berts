"""Verify evaluated trim contact at both cape edges and no rear band."""
import json
from pathlib import Path
import sys
import bpy
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog,cache_key
from fdm_sculpt.atelier import engine_hash
d=catalog()


def geometry(ref):
    definition=d[ref];directory=ROOT/'out/part-cache'/cache_key(definition,engine_hash(definition))
    record=json.loads((directory/'asset.json').read_text())
    with bpy.data.libraries.load(str(directory/'part.blend'),link=True) as (_,loaded):
        loaded.collections=[record['visual_collection']]
    verts=[];faces=[]
    for obj in loaded.collections[0].objects:
        offset=len(verts)
        verts.extend(obj.matrix_basis@v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in p.vertices] for p in obj.data.polygons)
    return verts,BVHTree.FromPolygons(verts,faces)

for suffix in ('','-b','-c','-d','-e'):
    vertices,trim=geometry('aurelian.mail-skirt-trim'+suffix+'@6')
    _,cape=geometry('aurelian.cape'+suffix+'@2')
    assert abs(max(v.z for v in vertices)+1.25)<1e-5
    contacts=[v for v in vertices if cape.find_nearest(v)[3]<.0001]
    assert any(v.x<0 for v in contacts) and any(v.x>0 for v in contacts),suffix
    for vertex in vertices:
        point,normal,_,distance=cape.find_nearest(vertex)
        assert distance<.0001 or (vertex-point).dot(normal)>=-.0001,suffix
    assert .49 < max(v.y for v in vertices) <= .50001
    print(suffix,'contacts',len(contacts),'rear',max(v.y for v in vertices))
print('TRIM_CAPE_CONTACT_VERIFIED')
