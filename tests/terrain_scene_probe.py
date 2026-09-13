"""Run with Blender --background --python to probe cached visual base geometry.

This is a visual geometry check, not a mesh printability or slicing audit.
Every asset must already have been compiled through atelier.
"""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from fdm_sculpt.atelier import engine_hash
from fdm_sculpt.components.parts import catalog,cache_key
from fdm_sculpt.army import load_assembly


def main():
    definitions=catalog()
    golden=json.loads((ROOT/'tests/fixtures/terrain-v3-golden.json').read_text())
    report={}
    for ref,digest in golden.items():
        d=definitions[ref]
        assert d.sha256==digest
        directory=ROOT/'out/part-cache'/cache_key(d,engine_hash(d))
        record=json.loads((directory/'asset.json').read_text())
        with bpy.data.libraries.load(str(directory/'part.blend'),link=True) as (_,loaded):
            loaded.collections=[record['visual_collection']]
        objects=list(loaded.collections[0].objects)
        assert len(objects)==1
        obj=objects[0]
        vertices=[obj.matrix_basis@v.co for v in obj.data.vertices]
        tree=BVHTree.FromPolygons(vertices,[list(p.vertices) for p in obj.data.polygons])
        p=d.to_dict()['parameters']['recipe']
        lo=[min(v[i] for v in vertices) for i in range(3)]
        hi=[max(v[i] for v in vertices) for i in range(3)]
        assert lo[0]>=-p['width']/2-1e-5 and hi[0]<=p['width']/2+1e-5
        assert lo[1]>=-p['length']/2-1e-5 and hi[1]<=p['length']/2+1e-5
        checks=dict(footprint=True)
        if d.family=='base-body':
            assert abs(lo[2])<1e-5 and abs(hi[2]-p['thickness'])<1e-5
            radius=(int(p['magnet'][0])+.2)/2
            for x,y in p['centers']:
                hit=tree.ray_cast((x,y,-1),(0,0,1))[0]
                assert hit is not None and abs(hit.z-1.1)<1e-5
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    wall=tree.ray_cast((x,y,.5),(dx,dy,0))[0]
                    assert wall is not None and abs((wall.x-x)*dx+(wall.y-y)*dy-radius)<1e-5
                hit=tree.ray_cast((x+radius+.1,y,-1),(0,0,1))[0]
                assert hit is not None and abs(hit.z)<1e-5
            checks.update(bottom_open=True,pocket_diameter=True,pocket_depth=True,roof_stock=True)
        else:
            assert abs(lo[2]+.15)<1e-5,(ref,lo,hi)
            for x0,y0,x1,y1 in p['boots']:
                for u in (.05,.25,.5,.75,.95):
                    for v in (.05,.25,.5,.75,.95):
                        x,y=x0+(x1-x0)*u,y0+(y1-y0)*v
                        if abs(x)>=p['width']/2 or abs(y)>=p['length']/2:continue
                        hit=tree.ray_cast((x,y,10),(0,0,-1))[0]
                        assert hit is not None and hit.z<=.01501,(ref,x,y,hit)
            checks.update(body_overlap=True,boot_clearance=True)
        report[ref]=dict(checks=checks,bounds=[lo,hi],definition_sha256=digest)
    boot_checks={}
    baseline=json.loads((ROOT/'tests/fixtures/terrain-migration-baseline.json').read_text())
    legs={}
    for name in baseline:
        assembly=load_assembly(ROOT/f'specs/{name}.json',definitions)
        count=0
        for placement in assembly['placements']:
            d=definitions[placement['part']]
            roles=[r for r in d.output_roles if r.endswith('_sole')]
            if not roles:continue
            if d.reference not in legs:
                directory=ROOT/'out/part-cache'/cache_key(d,engine_hash(d))
                record=json.loads((directory/'asset.json').read_text())
                with bpy.data.libraries.load(str(directory/'part.blend'),link=True) as (_,loaded):
                    loaded.collections=[record['visual_collection']]
                legs[d.reference]=[o for o in loaded.collections[0].objects if o.get('component_geometry_role') in roles]
            for obj in legs[d.reference]:
                frame=Matrix(placement['mount'])@obj.matrix_basis
                heights=[(frame@v.co).z for v in obj.data.vertices]
                assert min(heights)<2.015 and max(heights)>2.1,(name,placement['instance_id'],min(heights),max(heights))
                count+=1
        boot_checks[name]=count
    (ROOT/'out/terrain-geometry-check.json').write_text(json.dumps(dict(passes=True,parts=report,grounded_visible_soles=boot_checks),indent=2)+'\n')
    print('TERRAIN_VISUAL_GEOMETRY_VERIFIED',len(report))


if __name__=='__main__':main()
