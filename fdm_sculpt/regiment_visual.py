"""Fast visual assembly: local Exact cuts, no manufacturing union or export."""
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from . import blender_backend as bb


def finish_visual(job, context, sources, plans):
    output = Path(job["output"])
    scene = context.scene
    preview = bpy.data.collections.new("VISUAL_PREVIEW")
    scene.collection.children.link(preview)
    print("REGIMENT_EVALUATING_LOCAL_DETAILS", flush=True)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = []
    for source in sources:
        mesh = bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph), depsgraph=depsgraph)
        obj = bpy.data.objects.new("preview__"+source.name, mesh)
        preview.objects.link(obj)
        obj.matrix_world = source.matrix_world.copy()
        for key in source.keys():
            obj[key] = source[key]
        obj["visual_source_object"] = source.name
        obj["export_geometry"] = False
        obj["status"] = "visual preview only; overlapping parts; not print validated"
        objects.append(obj)
    context.source_root.hide_viewport = True
    context.source_root.hide_render = True
    scene["regiment_mode"] = "visual-preview"
    scene["digitally_validated"] = False
    scene["assembly_order_json"] = json.dumps([o.name for o in sources])
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.region_3d.view_distance = 30
                space.region_3d.view_location = (0, 0, 6)
                space.region_3d.view_rotation = Vector((0.6,-1.8,0.7)).to_track_quat("Z","Y")
                space.clip_end = 1000
                space.shading.type = "SOLID"
                space.shading.color_type = "MATERIAL"
                space.shading.show_cavity = True
                space.overlay.show_floor = False
                space.overlay.show_extras = False
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    # Save the orbitable review before spending any time on optional images.
    bpy.ops.wm.save_as_mainfile(filepath=str(output/"internal/elf-spearman-proof.blend"))
    print("REGIMENT_VISUAL_SCENE_SAVED", flush=True)
    if job.get("renders", True):
        camera = bb._ensure_camera(scene)
        views = {"three-quarter": ((0.8,-1.8,0.8), (0,0,6.5), 24)}
        atoms = {a["role"]: a for a in plans[2]["atoms"]}
        for name, role, focus, scale in (
            ("mail-tunic-detail", "torso", (0,-0.5,5.65), 4.2),
            ("helmet-detail", "helmet_crown", (0,-0.4,8.2), 4.5),
        ):
            matrix = Matrix(atoms[role].get("frame_mm", Matrix.Identity(4)))
            views[name] = (tuple(matrix.to_3x3() @ Vector((0.3,-1,0.25))),
                           tuple(matrix @ Vector(focus)), scale)
        for name, (direction, focus, scale) in views.items():
            bb._render_preview(scene, camera, objects, output/"previews"/(name+".png"),
                               view_direction=direction, focus_center=focus, ortho_scale=scale)
    (output/"visual-review.json").write_text(json.dumps(dict(
        mode="visual-preview", digitally_validated=False, seed=job["spec"]["seed"],
        label="visual preview only; overlapping parts; not print validated",
        object_count=len(objects), local_operations="ordered Exact CSG",
        omitted=["full-strip union", "mesh printability checks", "slicing", "same-seed geometry repeat"],
    ), indent=2)+"\n")
    print("REGIMENT_BUILD_COMPLETE", flush=True)
