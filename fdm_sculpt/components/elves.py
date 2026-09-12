"""Original elf proof recipes; millimetres, no Blender dependencies.

These revisions are proof candidates pending user art approval. The definition
contains the complete ordered primitive/CSG recipe consumed by the adapter.
"""
from __future__ import annotations

import math
from typing import Any

from .core import (ComponentDefinition, ComponentInstanceSpec, ComponentBuildResult,
                   ComponentLibrary, ComponentLibraryError, component_digest)


def _definition(pose: str) -> ComponentDefinition:
    atoms: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []

    def atom(role, primitive, **kwargs):
        atoms.append(dict(role=role, primitive=primitive, export=True, **kwargs))

    def box(role, dims, loc, bevel=0.04, **kw):
        atom(role, "cube", dimensions=dims, location=loc, bevel=bevel, **kw)

    def ell(role, dims, loc):
        atom(role, "sphere", dimensions=dims, location=loc, segments=16, ring_count=8)

    def rod(role, start, end, radius):
        atom(role, "between", start=start, end=end, radius=radius, bevel=0.03)

    def cone(role, r1, r2, depth, loc, scale=(1, 1, 1), vertices=16):
        atom(role, "cone", radius1=r1, radius2=r2, depth=depth,
             location=loc, scale=scale, vertices=vertices, bevel=0.0,
             rotation=(0, 0, math.pi/vertices))

    # Local soles at zero. Each pose articulates actual knee and ankle axes.
    legs = {}
    for side, sign in (("left", -1), ("right", 1)):
        stride = (0.25 * sign if pose == "c" else 0.0)
        ankle = (sign * (0.60 if pose == "b" else 0.53), stride, 0.72)
        knee = (sign * (0.70 if pose == "b" else 0.52),
                -0.30 if pose == "b" else stride * 0.4, 2.25)
        hip = (sign * 0.46, 0.0, 3.75)
        heel = (ankle[0], ankle[1] + 0.15, 0.22)
        toe = (ankle[0] + sign * 0.07, ankle[1] - 0.39, 0.22)
        legs[side] = dict(hip=hip, knee=knee, ankle=ankle, heel=heel, toe=toe,
                         femur_axis=[knee[i]-hip[i] for i in range(3)],
                         shin_axis=[ankle[i]-knee[i] for i in range(3)],
                         foot_axis=[toe[i]-heel[i] for i in range(3)])
        box(side+"_sole", (0.88, 1.28, 0.35), (ankle[0], ankle[1]-0.12, 0.10))
        box(side+"_toe", (0.85, 0.90, 0.35), toe)
        ell(side+"_ankle", (0.80, 0.82, 0.90), ankle)
        rod(side+"_shin", ankle, knee, 0.43)
        ell(side+"_knee", (0.88, 0.93, 0.92), knee)
        rod(side+"_thigh", knee, hip, 0.48)
        ell(side+"_hip", (1.02, 1.02, 1.15), hip)

    # A planted cloak makes arms and skirt self-supporting. Front remains open
    # below the skirt to show the legs and a deliberate inter-leg gap.
    cone("cloak", 1.02, 0.85, 5.85, (0, 0.63, 2.85), scale=(1, 0.50, 1))
    cone("skirt_core", 1.10, 0.78, 2.0, (0, 0, 3.7), scale=(1, 0.67, 1))
    cone("skirt_rising_underlay", 0.82, 1.15, 0.65, (0, -0.025, 2.65), scale=(1, 0.72, 1))
    for index, z in enumerate((2.95, 3.48, 4.01)):
        cone(f"skirt_lame_{index}", 1.15-(index*.08), 0.91-(index*.08),
             0.65, (0, -0.025, z), scale=(1, 0.72, 1))
    cone("torso", 0.75, 1.02, 1.90, (0, 0, 5.25), scale=(1, 0.69, 1))
    cone("cuirass_lower", 0.83, 1.03, 0.8, (0, -0.10, 4.93), scale=(1, 0.76, 1))
    cone("cuirass_upper", 0.88, 1.08, 0.85, (0, -0.13, 5.65), scale=(1, 0.76, 1))
    box("collar", (1.30, 0.94, 0.80), (0, 0, 6.35), bevel=0.12)
    # Deliberately planar face: no eye dots or unsupported ears at this scale.
    ell("cranium", (1.17, 1.12, 1.40), (0, 0, 7.30))
    box("chin", (0.77, 0.84, 0.57), (0, -0.12, 6.91), bevel=0.14)
    cone("nose_plane", 0.24, 0.13, 0.70, (0, -0.52, 7.43), scale=(0.85,1.20,1), vertices=4)
    box("brow", (1.22, 1.14, 0.30), (0, -0.04, 8.01), bevel=0.05)
    cone("helmet_crown", 0.72, 0.30, 1.36, (0, 0.05, 8.82), scale=(1, 0.90, 1))
    # Ear guards slope up out of the collar and visually lengthen the helmet.
    for sign in (-1, 1):
        box(f"temple_{sign}", (0.35, 0.82, 1.33), (sign*0.53, 0.02, 7.59), bevel=0.07)
    # Shield is a true lens formed by Exact intersection of two cylinder
    # primitives. Constant 0.86 mm plate depth, elongated leaf perimeter.
    for role, x, export in (("shield", -4.52, True), ("shield_lens_mask", 3.48, False)):
        atom(role, "cylinder", radius=4.65, depth=0.86,
             location=(x, -0.97, 3.12), axis="Y", vertices=64, bevel=0.0)
        atoms[-1]["export"] = export
    operations.append(dict(target="shield", operand="shield_lens_mask", operation="INTERSECT", solver="EXACT"))
    cone("shield_ground_heel", 0.53, 0.36, 1.35, (-0.52, -1.00, 0.50), scale=(1,0.85,1))
    box("shield_spine", (0.30, 0.35, 4.45), (-0.52, -1.50, 3.04), bevel=0.04)
    # Two rising braces are concealed as shield rim clasps, with 0.3+ stock.
    rod("shield_spear_brace", (-0.25, -0.97, 3.10), (1.20, -0.76, 4.50), 0.40)
    rod("spear", (1.20, -0.76, -0.15), (1.20, -0.76, 10.85), 0.51)
    cone("spear_leaf_lower", 0.39, 0.70, 0.58, (1.20, -0.76, 10.74), scale=(1, 0.67, 1))
    cone("spear_leaf_tip", 0.70, 0.34, 1.00, (1.20, -0.76, 11.50), scale=(1, 0.85, 1))
    # Hands are rounded palms, grouped fingers, thumbs and cuffs, fully fused.
    for side, shoulder, elbow, grip in (
        ("right", (0.86, 0, 5.98), (1.0, -0.10, 5.02 if pose != "b" else 4.85), (1.15, -0.72, 5.40)),
        ("left", (-0.86, 0, 5.98), (-1.05, -0.18, 5.13), (-0.72, -0.66, 4.90))):
        rod(side+"_sleeve_root", (0.68 if side=="right" else -0.68, 0.24, 3.95), elbow, 0.42)
        rod(side+"_upper_arm", shoulder, elbow, 0.44)
        ell(side+"_elbow", (0.94, 0.94, 0.94), elbow)
        rod(side+"_forearm", elbow, grip, 0.40)
        ell(side+"_pauldron", (1.10, 1.12, 0.95), shoulder)
        ell(side+"_palm", (0.94, 0.96, 0.98), (grip[0]-0.035,grip[1]+0.035,grip[2]))
        box(side+"_grouped_fingers", (0.77, 0.36, 0.64), (grip[0],grip[1]-0.29,grip[2]), bevel=0.10)
        ell(side+"_thumb", (0.45, 0.53, 0.58), (grip[0]-0.25,grip[1]-0.08,grip[2]+0.16))
        cone(side+"_cuff", 0.27, 0.46, 0.70, (grip[0],grip[1]+0.10,grip[2]-0.20), scale=(1,0.85,1))
    outputs = tuple(a["role"] for a in atoms if a["export"])
    return ComponentDefinition(
        component_id=f"aurelian.spearman.{pose}", version=1,
        name=f"Aurelian leafguard pose {pose.upper()}", family="elf-proof",
        required_anchors=("sole",), semantic_slots=("mono",), output_roles=outputs,
        parameters=dict(atoms=atoms, operations=operations, legs=legs,
                        sole_to_eye_mm=8.0, helmet_tip_mm=9.5, spear_tip_mm=12.0,
                        structural_wall_mm=0.75, spear_diameter_mm=1.02,
                        relief_mm=0.25, intentional_gap_mm=0.5,
                        adapter_version=1, union="ordered-exact-collection",
                        numerical_weld_mm=0.00001,
                        status="proof-candidate-awaiting-user-review"))


ELF_DEFINITIONS = tuple(_definition(pose) for pose in "abc")


def resolve_elf(definition: ComponentDefinition, instance: ComponentInstanceSpec) -> dict:
    if instance.reference != definition.reference:
        raise ComponentLibraryError("component reference mismatch")
    if set(instance.anchors) != {"sole"} or set(instance.semantic_bindings) != {"mono"}:
        raise ComponentLibraryError("elf requires sole anchor and mono semantic binding")
    anchor = instance.anchors["sole"]
    if tuple(anchor.scale) != (1, 1, 1):
        raise ComponentLibraryError("proof dimensions cannot be scaled")
    if any(anchor.rotate_deg):
        raise ComponentLibraryError("upright proof requires an unrotated sole frame")
    parameters = definition.to_dict()["parameters"]
    for atom in parameters["atoms"]:
        if "frame_mm" in atom:
            # Revision 2 poses rigid primitive frames before assembly placement.
            for i,value in enumerate(anchor.translate_mm):
                atom["frame_mm"][i][3] = round(atom["frame_mm"][i][3]+value,9)
            continue
        for key in ("location", "start", "end"):
            if key in atom:
                atom[key] = [round(v+t, 9) for v,t in zip(atom[key], anchor.translate_mm)]
    return dict(definition_sha256=definition.sha256, instance=instance.to_dict(), **parameters)


def build_elf(builder, definition, instance):
    plan = resolve_elf(definition, instance)
    digest = component_digest(plan)
    objects = {}
    for atom in plan["atoms"]:
        args = dict(atom)
        role = args.pop("role")
        primitive = args.pop("primitive")
        obj = builder.recipe_atom(f"{instance.instance_id}_{role}", primitive,
                                  instance.semantic_bindings["mono"], args)
        for key,value in dict(component_id=definition.component_id,
                              component_version=definition.version,
                              component_instance_id=instance.instance_id,
                              component_definition_sha256=definition.sha256,
                              component_plan_sha256=digest,
                              component_geometry_role=role).items():
            obj[key] = value
        objects[role] = obj
    for op in plan["operations"]:
        builder.boolean(objects[op["target"]], objects[op["operand"]], op["operation"])
    return ComponentBuildResult(definition, instance,
                                tuple((r,objects[r]) for r in definition.output_roles), digest)


ELF_LIBRARY = ComponentLibrary()
for _entry in ELF_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v2 import make_definitions
ELF_V2_DEFINITIONS = make_definitions(ELF_DEFINITIONS)
for _entry in ELF_V2_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v3 import make_definitions as make_v3_definitions
ELF_V3_DEFINITIONS = make_v3_definitions(ELF_V2_DEFINITIONS)
for _entry in ELF_V3_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v4 import make_definitions as make_v4_definitions
ELF_V4_DEFINITIONS = make_v4_definitions(ELF_V3_DEFINITIONS)
for _entry in ELF_V4_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v5 import make_definitions as make_v5_definitions
ELF_V5_DEFINITIONS = make_v5_definitions(ELF_V4_DEFINITIONS)
for _entry in ELF_V5_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v6 import make_definitions as make_v6_definitions
ELF_V6_DEFINITIONS = make_v6_definitions(ELF_V5_DEFINITIONS)
for _entry in ELF_V6_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v7 import make_definitions as make_v7_definitions
ELF_V7_DEFINITIONS = make_v7_definitions(ELF_V6_DEFINITIONS)
for _entry in ELF_V7_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v8 import make_definitions as make_v8_definitions
ELF_V8_DEFINITIONS = make_v8_definitions(ELF_V7_DEFINITIONS)
for _entry in ELF_V8_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v9 import make_definitions as make_v9_definitions
ELF_V9_DEFINITIONS = make_v9_definitions(ELF_V8_DEFINITIONS)
for _entry in ELF_V9_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v10 import make_definitions as make_v10_definitions
ELF_V10_DEFINITIONS = make_v10_definitions(ELF_V9_DEFINITIONS)
for _entry in ELF_V10_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
from .elves_v11 import make_definitions as make_v11_definitions
ELF_V11_DEFINITIONS = make_v11_definitions(ELF_V10_DEFINITIONS)
for _entry in ELF_V11_DEFINITIONS:
    ELF_LIBRARY.register(_entry, build_elf)
ELF_LIBRARY.freeze()
