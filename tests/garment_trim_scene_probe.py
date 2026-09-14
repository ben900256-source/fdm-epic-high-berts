"""Check visible trim creases against the evaluated garment surfaces."""
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from fdm_sculpt.components.parts import catalog,cache_key
from fdm_sculpt.atelier import engine_hash
d=catalog()


def tree(ref):
    definition=d[ref];directory=ROOT/'out/part-cache'/cache_key(definition,engine_hash(definition))
    record=json.loads((directory/'asset.json').read_text())
    with bpy.data.libraries.load(str(directory/'part.blend'),link=True) as (_,loaded):
        loaded.collections=[record['visual_collection']]
    verts=[];faces=[]
    for obj in loaded.collections[0].objects:
        offset=len(verts)
        verts.extend(obj.matrix_basis@v.co for v in obj.data.vertices)
        faces.extend([offset+i for i in p.vertices] for p in obj.data.polygons)
    return BVHTree.FromPolygons(verts,faces)


report={}
for kind,parent,bottom in [('tunic','aurelian.archer-tunic@4',-3.5),('mail-skirt','aurelian.skirt@3',-4.85)]:
    trim=tree('aurelian.'+kind+'-trim@2');garment=tree(parent)
    for z in (bottom+.65,(bottom-.5)/2,-1.1):
        center=trim.ray_cast((0,-10,z),(0,1,0))[0]
        edge=trim.ray_cast((.22,-10,z),(0,1,0))[0]
        ground=garment.ray_cast((0,-10,z),(0,1,0))[0]
        assert center is not None and edge is not None and ground is not None
        assert center.y>edge.y+.035,(kind,z,center,edge)
        assert center.y<ground.y-.015,(kind,z,center,ground)
    for i in range(24):
        angle=(i+.37)*math.tau/24
        direction=Vector((math.cos(angle),math.sin(angle),0))
        start=direction*4;start.z=bottom+.25
        surface=trim.ray_cast(start,-direction)[0]
        ground=garment.ray_cast(start,-direction)[0]
        assert surface is not None and ground is not None
        assert (surface-start).length<(ground-start).length-.015,(kind,i,surface,ground)
    report[kind]=dict(front_crease=True,hem_crease_clear_of_garment=True)
(ROOT/'out/garment-trim-geometry-check.json').write_text(json.dumps(dict(passes=True,parts=report),indent=2)+'\n')
print('GARMENT_TRIM_CREASES_VERIFIED')
