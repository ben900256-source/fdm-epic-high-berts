"""Read-only verification after reopening the saved procedural Blender scene."""
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fdm_sculpt.components.core import component_digest
from fdm_sculpt.components.elves import ELF_LIBRARY, resolve_elf
from fdm_sculpt.regiment_spec import RegimentSpec


def verify(output):
    internal = output/"internal"
    spec = RegimentSpec.load(internal/"regiment-spec.json")
    source = bpy.data.collections["SOURCE_PRIMITIVES"]
    export = bpy.data.collections["EVALUATED_EXPORT"]
    checks = dict(source_hidden=source.hide_viewport and source.hide_render,
                  one_export=len([o for o in export.all_objects if o.type=="MESH"])==1,
                  millimeters=abs(bpy.context.scene.unit_settings.scale_length-0.001)<1e-9)
    assembly = bpy.data.objects["elf_assembly_exact_source"]
    checks["assembly_operation_order"] = [m.type for m in assembly.modifiers] == ["BOOLEAN","WELD"]
    checks["assembly_exact"] = assembly.modifiers[0].solver=="EXACT" and assembly.modifiers[0].operation=="UNION"
    checks["declared_numerical_weld"] = abs(assembly.modifiers[1].merge_threshold-0.00001)<1e-10
    records = []
    for instance in spec.instances:
        definition = ELF_LIBRARY.resolve(instance.component_id,instance.version)
        plan = resolve_elf(definition,instance)
        objects = [o for o in source.all_objects if o.get("component_instance_id")==instance.instance_id]
        roles = {o.get("component_geometry_role"):o for o in objects}
        valid = len(objects)==len(plan["atoms"])==len(roles)
        center_errors = []
        for atom in plan["atoms"]:
            obj = roles.get(atom["role"])
            valid = valid and obj is not None
            if obj is None:
                continue
            valid = valid and all(obj.get(k)==v for k,v in dict(
                component_id=definition.component_id,component_version=definition.version,
                component_definition_sha256=definition.sha256,
                component_plan_sha256=component_digest(plan),export_geometry=atom["export"]).items())
            center = atom.get("location")
            if center is None:
                center = [(a+b)/2 for a,b in zip(atom["start"],atom["end"])]
            if "frame_mm" in atom:
                matrix = atom["frame_mm"]
                center = [sum(matrix[i][j]*center[j] for j in range(3))+matrix[i][3] for i in range(3)]
            # Hidden collections are excluded from the reopened dependency
            # graph: matrix_world may still be identity until made visible.
            # These source primitives are unparented, so matrix_basis is the
            # persisted transform and can be verified without unhiding them.
            valid = valid and obj.parent is None
            error = max(abs(obj.matrix_basis.translation[i]-center[i]) for i in range(3))
            center_errors.append(error)
            valid = valid and error<0.00001
            if "bevel_segments" in atom:
                bevels=[m for m in obj.modifiers if m.type=="BEVEL"]
                valid = valid and len(bevels)==1 and bevels[0].segments==atom["bevel_segments"] and abs(bevels[0].width-atom["bevel"])<1e-6
        for target_role in dict.fromkeys(op["target"] for op in plan["operations"]):
            target = roles[target_role]
            operations = [op for op in plan["operations"] if op["target"]==target_role]
            booleans = [m for m in target.modifiers if m.type=="BOOLEAN"]
            valid = valid and len(booleans)==len(operations)
            for modifier,operation in zip(booleans,operations):
                valid = valid and modifier.solver=="EXACT" and modifier.operation==operation["operation"] and modifier.object==roles[operation["operand"]]
        checks[instance.instance_id] = bool(valid)
        records.append(dict(instance_id=instance.instance_id,source_objects=len(objects),
                            definition_sha256=definition.sha256,plan_sha256=component_digest(plan),
                            maximum_primitive_center_error_mm=max(center_errors)))
    result = dict(checks=checks,instances=records,passes=all(checks.values()),
                  method="reopened saved Blender scene; retained primitive roles, hashes and Exact modifier operands")
    (internal/"saved-provenance.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    if not result["passes"]:
        raise ValueError("saved Blender provenance verification failed")
    print("REGIMENT_PROVENANCE_VERIFIED")


if __name__ == "__main__":
    verify(Path(sys.argv[sys.argv.index("--")+1]))
