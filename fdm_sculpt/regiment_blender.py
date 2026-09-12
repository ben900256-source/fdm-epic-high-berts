"""Blender-only adapter for the proof; reuses the existing primitive boundary."""
import json
from pathlib import Path

import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

from . import blender_backend as bb
from .components.elves import ELF_LIBRARY, resolve_elf
from .regiment_spec import RegimentSpec


class ElfBuilder(bb._PartBuilder):
    def boolean(self, target, cutter, operation="DIFFERENCE", **kwargs):
        if hasattr(self, "deferred_booleans"):
            self.deferred_booleans.append((target, cutter, operation, kwargs))
            return None
        return super().boolean(target, cutter, operation, **kwargs)

    def recipe_atom(self, role, primitive, semantic, args):
        args = dict(args)
        rigid_frame = args.pop("frame_mm", None)
        scale = args.pop("scale", (1, 1, 1))
        rotation = args.pop("rotation", None) if primitive == "cone" else None
        bevel = args.pop("bevel", 0) if primitive == "cone" else None
        bevel_segments = args.pop("bevel_segments", 2) if primitive == "cone" else None
        obj = getattr(self, primitive)(role, semantic=semantic, **args)
        if primitive == "cone":
            obj.modifiers.clear()
            if rotation:
                obj.rotation_euler = rotation
            if bevel:
                self.bevel(obj, bevel, segments=bevel_segments)
        if tuple(scale) != (1, 1, 1):
            obj.scale = scale
            bb._active(obj)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if rigid_frame is not None:
            parent = Matrix.Translation(self.origin)
            obj.matrix_world = parent @ Matrix(rigid_frame) @ parent.inverted() @ obj.matrix_world
        return obj


def _ray_thickness(tree, start, direction):
    origin, direction = Vector(start), Vector(direction).normalized()
    first, *_ = tree.ray_cast(origin, direction, 100)
    if first is None:
        return None
    second, *_ = tree.ray_cast(first+direction*0.0001, direction, 100)
    return round((second-first).length, 6) if second is not None else None


def measurements(master, spec, head_trees=None):
    tree = BVHTree.FromPolygons([master.matrix_world @ v.co for v in master.data.vertices],
                               [tuple(p.vertices) for p in master.data.polygons])
    probes = []
    # Each measurement crosses the evaluated fused solid, not nominal inputs.
    for instance in spec.instances:
        x = instance.anchors["sole"].translate_mm[0]
        tests = (
            ("spear_shaft", (x-2, -0.76, 10.7), (1, 0, 0), 1.0),
            ("shield_wall", (x-0.85, -5, 4.1), (0, 1, 0), 0.75),
            ("cloak_wall", (x, 5, 2.0), (0, -1, 0), 0.75),
            ("neck_core", (x, -5, 7.4), (0, 1, 0), 0.75),
            ("right_grip", (x+1.15, -5, 6.4), (0, 1, 0), 0.75),
        )
        if instance.version in (2,3,4,5,6,7,8,9,10,11):
            plan = resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
            atoms = {a["role"]:a for a in plan["atoms"]}
            local_tests = (
                ("spear_shaft","spear",(-2,-0.76,9.7),(1,0,0),1.0),
                ("shield_wall","shield",(-0.85,-5,3.1),(0,1,0),0.75),
                ("cloak_wall","cloak",(0,5,1.0),(0,-1,0),0.75),
                ("neck_core","collar",(0,-5,6.4),(0,1,0),0.75),
                ("right_grip","right_palm",(1.15,-5,5.4),(0,1,0),0.75),
            )
            tests = []
            for feature,role,start,direction,minimum in local_tests:
                if instance.version in (3,4,5,6,7,8,9,10,11) and feature=="right_grip":
                    start = (atoms[role]["location"][0],-5,atoms[role]["location"][2])
                matrix = Matrix(atoms[role]["frame_mm"])
                tests.append((feature,tuple(matrix@Vector(start)),
                              tuple(matrix.to_3x3()@Vector(direction)),minimum))
        for feature, start, direction, minimum in tests:
            value = _ray_thickness(tree, start, direction)
            probes.append(dict(instance_id=instance.instance_id, feature=feature,
                               start_mm=start, direction=direction, measured_mm=value,
                               minimum_mm=minimum, passes=value is not None and value+1e-5 >= minimum))
    relief = []
    envelopes = []
    vertices = [master.matrix_world @ v.co for v in master.data.vertices]
    for instance in spec.instances:
        x = instance.anchors["sole"].translate_mm[0]
        front_start,field_start,direction = Vector((x-0.52,-5,4.1)),Vector((x-0.85,-5,4.1)),Vector((0,1,0))
        if instance.version in (2,3,4,5,6,7,8,9,10,11):
            plan = resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
            shield = next(a for a in plan["atoms"] if a["role"]=="shield")
            matrix = Matrix(shield["frame_mm"])
            front_start,field_start = matrix@Vector((-0.42,-5,3.1)),matrix@Vector((-0.85,-5,3.1))
            if instance.version in (8,9,10,11):
                emblem=plan["shield_insignia"]
                front_x,front_z=emblem["belly_probe_local"]
                field_x,field_z=emblem["field_probe_local"]
                front_start=matrix@Vector((front_x,-5,front_z))
                field_start=matrix@Vector((field_x,-5,field_z))
            direction = matrix.to_3x3()@direction
        front, *_ = tree.ray_cast(front_start,direction,10)
        field, *_ = tree.ray_cast(field_start,direction,10)
        value = float((field-front).dot(direction)) if front is not None and field is not None else None
        relief.append(dict(instance_id=instance.instance_id,measured_mm=value,minimum_mm=0.25,
                           passes=value is not None and value>=0.25-1e-5))
        above_base = [v.x for v in vertices if v.z>1.0001 and x-2<v.x<x+2]
        envelopes.append((min(above_base),max(above_base)))
    gaps = [round(right[0]-left[1],6) for left,right in zip(envelopes,envelopes[1:])]
    grasps = []
    for instance in spec.instances:
        if instance.version not in (3,4,5,6,7,8,9,10,11):
            continue
        plan = resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
        atoms = {a["role"]:a for a in plan["atoms"]}
        matrix = Matrix(atoms["spear"]["frame_mm"])
        grip_z = plan["spear_grip"]["center"][2]
        # Approach from the exposed spear side; a ray from the shield side
        # would measure the shield first on several of the turned poses.
        width = _ray_thickness(tree,matrix@Vector((2,-1.22,grip_z)),matrix.to_3x3()@Vector((-1,0,0)))
        direction = matrix.to_3x3()@Vector((0,1,0))
        front,*_ = tree.ray_cast(matrix@Vector((1.05,-5,grip_z+0.02)),direction,10)
        shaft_front = matrix@Vector((1.05,-1.27,grip_z+0.02))
        projection = (shaft_front-front).dot(direction) if front is not None else None
        grasps.append(dict(instance_id=instance.instance_id,finger_span_mm=width,
                           knuckle_projection_beyond_shaft_mm=projection,
                           passes=width is not None and width>=1.30 and projection is not None and projection>=0.25))
    elbows=[]
    helmet_backs=[]
    for instance in spec.instances:
        if instance.version not in (4,5,6,7,8,9,10,11):
            continue
        plan=resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
        atoms={a["role"]:a for a in plan["atoms"]}
        for side,sign in (("left",-1),("right",1)):
            guard=atoms[side+"_vambrace"]
            matrix=Matrix(guard["frame_mm"])
            local_z=plan["forearm_armor"]["extensions"][side]["elbow_local_z_mm"]
            width=_ray_thickness(tree,matrix@Vector((sign*0.85,0,local_z)),
                                 matrix.to_3x3()@Vector((-sign,0,0)))
            elbows.append(dict(instance_id=instance.instance_id,side=side,
                                measured_mm=width,minimum_mm=1.0,
                                passes=width is not None and width>=1.0))
        matrix=Matrix(atoms["helmet_crown"]["frame_mm"])
        direction=matrix.to_3x3()@Vector((0,-1,0))
        rear,*_=tree.ray_cast(matrix@Vector((0,5,7.50)),direction,10)
        skull_back=matrix@Vector((0,0.56,7.50))
        projection=(skull_back-rear).dot(direction) if rear is not None else None
        helmet_backs.append(dict(instance_id=instance.instance_id,
                                  rear_cover_projection_mm=projection,minimum_mm=0.25,
                                  passes=projection is not None and projection>=0.25))
    wrist_joins=[]
    for instance in spec.instances:
        if instance.version not in (5,6,7,8,9,10,11):
            continue
        plan=resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
        bridge=next(a for a in plan["atoms"] if a["role"]=="right_wrist_bridge")
        matrix=Matrix(bridge["frame_mm"])
        width=_ray_thickness(tree,matrix@Vector((2,0,0)),matrix.to_3x3()@Vector((-1,0,0)))
        wrist_joins.append(dict(instance_id=instance.instance_id,measured_mm=width,minimum_mm=0.90,
                                passes=width is not None and width>=0.90))
    cape_shoulders=[]
    for instance in spec.instances:
        if instance.version not in (8,9,10,11):
            continue
        plan=resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
        cloth=next(a for a in plan["atoms"] if a["role"]=="cape_left_shoulder_drape")
        matrix=Matrix(cloth["frame_mm"])
        direction=matrix.to_3x3()@Vector((0,-1,0))
        for side,sign in (("left",-1),("right",1)):
            start=matrix@Vector((sign*0.90,5,6.10))
            width=_ray_thickness(tree,start,direction)
            rear,*_=tree.ray_cast(start,direction,10)
            shoulder_plane=matrix@Vector((sign*0.90,0,6.10))
            projection=(shoulder_plane-rear).dot(direction) if rear is not None else None
            cape_shoulders.append(dict(instance_id=instance.instance_id,side=side,
                                       fused_thickness_mm=width,rear_drape_projection_mm=projection,
                                       minimum_thickness_mm=0.75,minimum_projection_mm=0.70,
                                       passes=width is not None and width>=0.75 and projection is not None and projection>=0.70))
    fitted_heads=[]
    for instance in spec.instances:
        if instance.version not in (10,11):
            continue
        plan=resolve_elf(ELF_LIBRARY.resolve(instance.component_id,instance.version),instance)
        matrix=Matrix(next(a for a in plan['atoms'] if a['role']=='cranium')['frame_mm'])
        direction=matrix.to_3x3()@Vector((0,1,0))
        landmarks=plan['face_landmarks']
        # Use the exported head recipe before assembly union for facial relief:
        # several posed spears otherwise occlude frontal measurement rays.
        head_tree=head_trees[instance.instance_id]
        filled=[]
        for point in [landmarks['brow_fill_probe_local']]+landmarks['temple_fill_probes_local']:
            hit,normal,*_=head_tree.ray_cast(matrix@Vector(point),direction,10)
            filled.append(hit is not None and normal.dot(direction)>0)
        front,*_=head_tree.ray_cast(matrix@Vector((0,-3,8.02)),direction,10)
        recess=None if front is None else (matrix.inverted()@front).y-(-0.848)
        eyes=[]
        for x in (-0.31,0.31):
            eye,*_=head_tree.ray_cast(matrix@Vector((x,-3,7.72)),direction,10)
            cheek,*_=head_tree.ray_cast(matrix@Vector((x,-3,7.36)),direction,10)
            eyes.append(None if eye is None or cheek is None else (eye-cheek).dot(direction))
        fitted_heads.append(dict(instance_id=instance.instance_id,filled_landmarks=filled,
                                 brow_front_recess_mm=recess,eye_recess_depths_mm=eyes,
                                 passes=all(filled) and recess is not None and 0<=recess<=0.25
                                        and all(v is not None and v>=0.25 for v in eyes)))
    return dict(method="evaluated solid BVH entry/exit rays and projected envelopes above strip",
                probes=probes,relief=relief,figure_gaps_mm=gaps,
                grasps=grasps,elbow_armor=elbows,helmet_backs=helmet_backs,wrist_joins=wrist_joins,
                cape_shoulders=cape_shoulders,fitted_heads=fitted_heads,
                passes=all(p["passes"] for p in probes+relief+grasps+elbows+helmet_backs+wrist_joins+cape_shoulders+fitted_heads) and min(gaps)>=0.5)


def run(job):
    spec = RegimentSpec.from_dict(job["spec"])
    output = Path(job["output"])
    internal = output / "internal"
    internal.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    bb._configure_scene(scene, 1400)
    context = bb._BuildContext(scene)
    part = dict(part_id="elf_strip", kind="regiment",
                variant="".join(i.component_id[-1] for i in spec.instances), position=[0,0,0])
    initial = context.begin_part(part)
    builder = ElfBuilder(context, part, initial.collection)
    if job["operation"] == "preview":
        builder.deferred_booleans = []
    base = builder.cube("strip", spec.strip_mm, (0,0,0.5), "ivory", bevel=0)
    sources = [base]
    plans = []
    # Build every instance independently from its pinned recipe. No copied mesh.
    for instance in spec.instances:
        definition = ELF_LIBRARY.resolve(instance.component_id, instance.version)
        result = ELF_LIBRARY.build(builder, instance)
        sources.extend(obj for _,obj in result.objects)
        plans.append(resolve_elf(definition, instance))
    (internal / "resolved-plans.json").write_text(json.dumps(plans, sort_keys=True, indent=2)+"\n")
    if job["operation"] == "preview":
        for target, cutter, operation, kwargs in builder.deferred_booleans:
            bb._PartBuilder.boolean(builder, target, cutter, operation, **kwargs)
        from .regiment_visual import finish_visual
        finish_visual(job, context, sources, plans)
        return
    # Retain the complete assembly expression, including its numerical closure
    # modifier, as procedural source. No edit-mode or mesh-element cleanup.
    operands = bpy.data.collections.new("ELF_ORDERED_UNION_OPERANDS")
    context.source_root.children.link(operands)
    for obj in sources[1:]:
        operands.objects.link(obj)
    expression = base.copy()
    expression.data = base.data.copy()
    expression.name = "elf_assembly_exact_source"
    expression["export_geometry"] = False
    expression["union_order_json"] = json.dumps([o.name for o in sources])
    context.source_root.objects.link(expression)
    union = expression.modifiers.new("01_exact_declared_union", "BOOLEAN")
    union.operation = "UNION"
    union.solver = "EXACT"
    union.operand_type = "COLLECTION"
    union.collection = operands
    union.use_self = True
    union.use_hole_tolerant = True
    weld = expression.modifiers.new("02_numerical_closure_0.00001mm", "WELD")
    weld.merge_threshold = plans[0]["numerical_weld_mm"]
    print("REGIMENT_EVALUATING_EXACT_UNION", flush=True)
    master = bb._bake_csg("Aurelian leafguard - fused proof strip", expression, (), "UNION", context.export_root)
    bb._active(master)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print("REGIMENT_EXACT_UNION_COMPLETE", flush=True)
    master.data.materials.clear()
    master.data.materials.append(context.materials["ivory"])
    master["role"] = "fused_printable_strip"
    master["construction"] = "ordered-exact-union-then-declared-numerical-weld"
    master["seed"] = spec.seed
    master["status"] = "internal proof - awaiting digital validation and user review"
    head_trees={}
    if all(i.version in (10,11) for i in spec.instances):
        depsgraph=bpy.context.evaluated_depsgraph_get()
        for obj in context.source_objects['elf_strip']:
            if obj.get('component_geometry_role')=='cranium':
                evaluated=obj.evaluated_get(depsgraph)
                head_trees[obj['component_instance_id']]=BVHTree.FromPolygons(
                    [evaluated.matrix_world@v.co for v in evaluated.data.vertices],
                    [tuple(p.vertices) for p in evaluated.data.polygons])
    context.source_root.hide_render = True
    context.source_root.hide_viewport = True
    for obj in context.source_objects["elf_strip"]:
        obj.hide_render = True
    metrics = bb._object_metrics(master)
    metrics["self_intersection_count"] = bb._self_intersection_count(master)
    metrics["features"] = measurements(master, spec, head_trees)
    metrics["blender_version"] = bpy.app.version_string
    metrics["seed"] = spec.seed
    print("REGIMENT_MESH_MEASURED", flush=True)
    # A readable scene even on a failed proof, so parameters can be revised.
    camera = bb._ensure_camera(scene)
    views = {
        "front": ((0,-1,0.10), (0,0,6.5), 24),
        "three-quarter": ((0.8,-1.8,0.8), (0,0,6.5), 24),
        "side": ((1,0,0.04), (0,0,6.5), 16),
        "face-grip-detail": ((0.25,-1,0.15), (0,-0.25,7.8), 6.0),
        "grip-detail": ((1,1,0.25), (1.1,-0.7,6.15), 3.5),
        "pose-detail": ((0.8,-1.8,0.35), (4,0,5.5), 11.5),
    }
    if all(i.version in (3,4,5,6,7,8,9,10,11) for i in spec.instances):
        grip = plans[2]["spear_grip"]["center"]
        matrix = Matrix(next(a for a in plans[2]["atoms"] if a["role"]=="spear")["frame_mm"])
        focus = tuple(matrix@Vector(grip))
        views.update({
            "grip-front": ((0.35,-1,0.2),focus,3.8),
            "grip-side": ((1,-0.4,0.15),focus,3.8),
            "cape-back": ((0,1,0.15),(0,0,5.3),24),
            "cape-detail": ((0.7,1,0.25),(0,0.5,4.4),9),
        })
    if all(i.version in (4,5,6,7,8,9,10,11) for i in spec.instances):
        elbow=plans[2]["arms"]["right"]["elbow"]
        anchor=spec.instances[2].anchors["sole"].translate_mm
        elbow_focus=tuple(a+b for a,b in zip(elbow,anchor))
        views["elbow-detail"] = ((1,0.65,0.25),elbow_focus,3.8)
        views["arm-profile"] = ((1,-0.15,0.1),(elbow_focus[0],elbow_focus[1],elbow_focus[2]+0.55),5.0)
        head_matrix=Matrix(next(a for a in plans[2]["atoms"] if a["role"]=="helmet_crown")["frame_mm"])
        views["helmet-back"] = ((0.4,1,0.1),tuple(head_matrix@Vector((0,0.2,7.5))),4.4)
        views["cape-top"] = ((0.3,1,0.3),(0,0.85,6.65),4.8)
        if all(i.version in (5,6,7,8,9,10,11) for i in spec.instances):
            views["helmet-crown"] = ((0.6,-1,0.2),tuple(head_matrix@Vector((0,0,8.3))),4.3)
            wrist=plans[2]["arms"]["right"]["wrist"]
            views["wrist-join"] = ((1,-0.05,0.25),tuple(a+b for a,b in zip(wrist,anchor)),3.3)
            if all(i.version in (6,7,8,9,10,11) for i in spec.instances):
                views["cape-front"] = ((0,-1,0.03),(0,0,2.4),7.5)
                views["cape-flare"] = ((0.8,-1,0.25),(0,0,2.4),8)
                views["elbow-blend"] = ((1,0.5,0.18),elbow_focus,3.5)
    if all(i.version in (8,9,10,11) for i in spec.instances):
        cloth=next(a for a in plans[2]["atoms"] if a["role"]=="cape_left_shoulder_drape")
        cape_focus=tuple(Matrix(cloth["frame_mm"])@Vector((0,0.45,6.0)))
        views["cape-shoulders"] = ((0.5,1,0.35),cape_focus,5.0)
        views["cape-shoulder-side"] = ((1,0.3,0.2),cape_focus,5.0)
        shield=next(a for a in plans[2]["atoms"] if a["role"]=="shield")
        shield_matrix=Matrix(shield["frame_mm"])
        views["seahorse-shield"] = (tuple(shield_matrix.to_3x3()@Vector((0,-1,0))),
                                    tuple(shield_matrix@Vector((-0.42,-1.40,3.2))),5.8)
    if all(i.version in (10,11) for i in spec.instances):
        head_matrix=Matrix(next(a for a in plans[2]['atoms'] if a['role']=='cranium')['frame_mm'])
        for name,direction in [('face-front',(0,-1,0.08)),('face-three-quarter',(-0.55,-1,0.10))]:
            views[name]=(tuple(head_matrix.to_3x3()@Vector(direction)),
                         tuple(head_matrix@Vector((0,-0.35,7.50))),3.5)
    if job.get("renders", True):
        for name,(direction,focus,scale) in views.items():
            bb._render_preview(scene, camera, [master], output/"previews"/(name+".png"),
                               view_direction=direction, focus_center=focus, ortho_scale=scale)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_distance = 30
                area.spaces.active.region_3d.view_location = (0,0,6)
                area.spaces.active.region_3d.view_rotation = Vector((0.6,-1.8,0.7)).to_track_quat("Z","Y")
                area.spaces.active.clip_end = 1000
                area.spaces.active.shading.type = "SOLID"
                area.spaces.active.shading.color_type = "MATERIAL"
                area.spaces.active.shading.show_cavity = True
                area.spaces.active.overlay.show_floor = False
    bb._active(master)
    bpy.ops.wm.save_as_mainfile(filepath=str(internal/"elf-spearman-proof.blend"))
    (internal / "mesh-metrics.json").write_text(json.dumps(metrics, sort_keys=True, indent=2)+"\n")
    if job["operation"] == "build":
        bb._export_stl(output/"elf-spearman-proof.stl", [master])
        metrics["stl_sha256"] = bb._sha256_file(output/"elf-spearman-proof.stl")
        (internal / "mesh-metrics.json").write_text(json.dumps(metrics, sort_keys=True, indent=2)+"\n")
    print("REGIMENT_BUILD_COMPLETE")
