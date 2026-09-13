"""Opt-in terrain adapter around the unchanged primitive atelier engine.

Only definitions with heightfield atoms depend on this worker's cache hash.
"""
from pathlib import Path
import json
import runpy
import sys

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from fdm_sculpt.components.heightfield import grid_mesh
from fdm_sculpt.regiment_blender import ElfBuilder


def heightfield(self,role,grid,semantic,export=True):
    vertices,faces,top_faces=grid_mesh(grid)
    mesh=bpy.data.meshes.new('procedural_heightfield')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new('procedural_heightfield',mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location=self.origin
    for polygon in mesh.polygons[:top_faces]:
        polygon.use_smooth=True
    return self.finish(obj,role,semantic,export=export)


if __name__=='__main__':
    ElfBuilder.heightfield=heightfield
    runpy.run_path(str(Path(__file__).with_name('atelier_blender.py')),run_name='__main__')
    command,path=sys.argv[sys.argv.index('--')+1:]
    if command=='verify':
        job=json.loads(Path(path).read_text())
        manifests=json.loads(bpy.context.scene['asset_manifest_json'])
        result_path=Path(job['output'])/'saved-provenance.json'
        result=json.loads(result_path.read_text())
        for ref,asset in job['assets'].items():
            for atom in asset['definition']['parameters']['atoms']:
                if atom['primitive']!='heightfield':continue
                source=bpy.data.collections[manifests[ref]['source_collection']]
                obj=next(o for o in source.objects if o['component_geometry_role']==atom['role'])
                vertices,faces,_=grid_mesh(atom['grid'])
                valid=(len(obj.data.vertices)==len(vertices) and len(obj.data.polygons)==len(faces)
                    and all(max(abs(a-b) for a,b in zip(v.co,p))<1e-6 for v,p in zip(obj.data.vertices,vertices))
                    and all(tuple(p.vertices)==tuple(face) for p,face in zip(obj.data.polygons,faces)))
                result['checks'][ref+'/sampled-source']=valid
        result['passes']=all(result['checks'].values())
        result_path.write_text(json.dumps(result,indent=2)+'\n')
        if not result['passes']:raise ValueError('saved procedural heightfield differs from pinned samples')
