"""Background Blender regression for cancelled row unions; no print validation."""
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fdm_sculpt.workshop_union_blender import apply_union

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add()
target=bpy.context.object
bpy.ops.mesh.primitive_plane_add(location=(0, 0, .5))
operand=bpy.context.object
bpy.context.view_layer.objects.active=target
boolean=target.modifiers.new('Rejected input', 'BOOLEAN')
boolean.solver='MANIFOLD'
boolean.operation='UNION'
boolean.object=operand
try:
    apply_union(target, boolean)
except RuntimeError as error:
    assert 'no STL was exported' in str(error)
else:
    raise AssertionError('A rejected Boolean must fail the export')
target.modifiers.clear()
bpy.data.objects.remove(operand, do_unlink=True)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
operand=bpy.context.object
bpy.context.view_layer.objects.active=target
boolean=target.modifiers.new('Accepted input', 'BOOLEAN')
boolean.solver='MANIFOLD'
boolean.operation='UNION'
boolean.object=operand
apply_union(target, boolean)
assert not target.modifiers
assert max(v.co.z for v in target.data.vertices)==2
print('Cancelled Boolean rejected; successful Boolean applied')
