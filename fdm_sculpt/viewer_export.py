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
        for obj in requested.collections[0].objects:
            mesh = obj.data
            mesh.calc_loop_triangles()
            matrix = obj.matrix_basis
            normal_matrix = matrix.to_3x3().inverted().transposed()
            for triangle in mesh.loop_triangles:
                normal = (normal_matrix @ triangle.normal).normalized()
                for index in triangle.vertices:
                    values.extend(matrix @ mesh.vertices[index].co)
                    values.extend(normal)
        if sys.byteorder != 'little':
            values.byteswap()
        target = Path(asset['target'])
        temporary = target.with_suffix('.tmp')
        temporary.write_bytes(values.tobytes())
        temporary.replace(target)
        print('VIEWER_EXPORTED '+asset['reference'], flush=True)


if __name__ == '__main__':
    export(json.loads(Path(sys.argv[-1]).read_text()))
