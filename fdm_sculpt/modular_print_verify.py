"""Reopen a trial scene and verify its packed source and exported mesh."""
import json
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt.atelier_blender import mesh_hash
from fdm_sculpt.blender_backend import _mesh_object_hash, _sha256_file

output = Path(sys.argv[sys.argv.index('--') + 1])
job = json.loads((output/'internal/assembly-job.json').read_text())
metrics = json.loads((output/'internal/mesh-metrics.json').read_text())
master, = bpy.data.collections['EVALUATED_EXPORT'].objects
checks = dict(assembly=json.loads(bpy.context.scene['assembly_json']) == job['assembly'],
              seed=bpy.context.scene['seed'] == job['seed'],
              fused_mesh=_mesh_object_hash(master) == metrics['mesh_hash'],
              stl=_sha256_file(output/'elf-spearman-proof.stl') == metrics['stl_sha256'],
              exact_order=json.loads(master['exact_union_order_json']) == json.loads((output/'internal/exact-union-order.json').read_text()),
              dependencies=all(lib.packed_file is not None for lib in bpy.data.libraries))
for ref, asset in job['assets'].items():
    manifest = asset['manifest']
    source = bpy.data.collections[manifest['source_collection']]
    visual = bpy.data.collections[manifest['visual_collection']]
    checks[ref] = (json.loads(source['definition_json']) == asset['definition'] and
                   {o['component_geometry_role']:mesh_hash(o) for o in visual.objects} == manifest['mesh_hashes'])
operations = json.loads((output/'internal/manufacturing-operations.json').read_text())
cache_file = output/'internal/manufacturing-cache.json'
if cache_file.exists():
    checks['manufacturing_cache'] = json.loads(bpy.context.scene['manufacturing_cache_json']) == json.loads(cache_file.read_text())
checks['manufacturing_operations'] = all(
    name in bpy.data.objects and json.loads(bpy.data.objects[name]['manufacturing_operation_json']) == operation
    for name, operation in operations.items())
result = dict(passes=all(checks.values()), checks=checks)
(output/'internal/manufacturing-provenance.json').write_text(json.dumps(result, indent=2))
assert result['passes'], result
print('MODULAR_PRINT_PROVENANCE_VERIFIED', flush=True)
