"""Read already baked visual collections into compact browser triangle buffers."""
import array
import json
from pathlib import Path
import sys

import bpy


def export(job):
    for asset in job['missing']:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        with bpy.data.libraries.load(asset['blend'], link=False) as (_, requested):
            requested.collections = [asset['collection']]
        values = array.array('f')
        pieces = []
        for obj in requested.collections[0].objects:
            mesh = obj.data
            mesh.calc_loop_triangles()
            matrix = obj.matrix_basis
            normal_matrix = matrix.to_3x3().inverted().transposed()
            first_triangle = len(values)//18
            for triangle in mesh.loop_triangles:
                normal = (normal_matrix @ triangle.normal).normalized()
                for index in triangle.vertices:
                    values.extend(matrix @ mesh.vertices[index].co)
                    values.extend(normal)
            if len(values)//18 > first_triangle:
                pieces.append(dict(role=obj.get('component_geometry_role',obj.name),
                                   first_triangle=first_triangle,
                                   triangle_count=len(values)//18-first_triangle))
        if sys.byteorder != 'little':
            values.byteswap()
        target = Path(asset['target'])
        temporary = target.with_suffix('.tmp')
        temporary.write_bytes(values.tobytes())
        temporary.replace(target)
        metadata = target.with_suffix('.json')
        temporary = metadata.with_suffix('.tmp')
        temporary.write_text(json.dumps(dict(pieces=pieces)))
        temporary.replace(metadata)
        print('VIEWER_EXPORTED '+asset['reference'], flush=True)


if __name__ == '__main__':
    export(json.loads(Path(sys.argv[-1]).read_text()))
