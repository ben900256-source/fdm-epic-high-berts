"""Confirm the visible forearm armor still meets the elbow and wrist cuff."""
import json
from pathlib import Path
import sys
import bpy
from mathutils.bvhtree import BVHTree

output = Path(sys.argv[-1])
job = json.loads((output/'assembly-job.json').read_text())
directory = Path(job['assets']['aurelian.left-arm@4']['directory'])
record = json.loads((directory/'asset.json').read_text())
with bpy.data.libraries.load(str(directory/'part.blend'), link=True) as (_, requested):
    requested.collections = [record['visual_collection']]
objects = {obj['component_geometry_role']:obj for obj in requested.collections[0].objects}
assert 'left_forearm' not in objects


def tree(role):
    obj = objects[role]
    vertices = [obj.matrix_basis @ v.co for v in obj.data.vertices]
    return BVHTree.FromPolygons(vertices, [list(p.vertices) for p in obj.data.polygons])


armor = tree('left_vambrace')
joins = {role:len(armor.overlap(tree(role))) for role in ('left_elbow_transition', 'left_cuff')}
report = dict(label='Visual arm contact only; not manufacturing validation',
              removed_role='left_forearm', crossing_faces=joins, passes=all(joins.values()))
(output/'arm-contact.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report), flush=True)
assert report['passes'], 'forearm armor has lost contact with elbow or cuff'
