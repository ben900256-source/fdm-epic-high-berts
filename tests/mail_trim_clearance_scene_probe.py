"""Verify the evaluated trim ends at the wrap and clears all five capes."""
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


vertices,trim=geometry('aurelian.mail-skirt-trim@4')
assert abs(max(v.z for v in vertices)+1.25)<1e-5
assert abs(min(v.z for v in vertices)+4.85)<1e-5
assert max(v.y for v in vertices)<=-.5+1e-5
for suffix in ('','-b','-c','-d','-e'):
    _,cape=geometry('aurelian.cape'+suffix+'@2')
    assert not trim.overlap(cape),suffix
report=dict(passes=True,wrap_stop_z_mm=-1.25,hem_bottom_z_mm=-4.85,capes_cleared=5)
(ROOT/'out/mail-trim-clearance-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('MAIL_TRIM_WRAP_AND_CAPES_VERIFIED')
