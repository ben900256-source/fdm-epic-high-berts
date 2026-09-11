"""Curved tapered helmets and rounded torso and shoulder anatomy."""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .elves_v2 import point
from .elves_v3 import axis_frame,lerp


def make_definitions(originals):
    definitions=[]
    for source in originals:
        if source.version!=6:
            raise ValueError("elf revision 7 derives only from pinned revision 6")
        p=deepcopy(source.to_dict()["parameters"])
        atoms=p["atoms"]
        roles={a["role"]:a for a in atoms}
        body_frame=p["frames"]["body"]
        # Rounded rib cage and formed breastplate follow the posed body frame;
        # overlapping shoulder slopes connect the neck, chest and upper arms.
        for role,dimensions,location in (
            ("torso",[2.16,1.46,2.28],[0,0.04,5.20]),
            ("cuirass_lower",[2.10,1.54,1.34],[0,-0.10,5.07]),
            ("cuirass_upper",[2.28,1.66,1.50],[0,-0.10,5.66]),
            ("collar",[1.42,1.02,0.84],[0,0,6.35]),
        ):
            shape=roles[role]
            shape.clear()
            shape.update(role=role,primitive="sphere",export=True,
                         dimensions=dimensions,location=location,segments=24,ring_count=16,
                         frame_mm=body_frame)
        shoulder_landmarks={}
        for side,sign in (("left",-1),("right",1)):
            arm=p["arms"][side]
            neck=point(body_frame,(sign*0.43,0.02,6.20))
            deltoid=lerp(arm["shoulder"],arm["elbow"],0.10)
            slope_frame,length=axis_frame(neck,deltoid)
            atoms.append(dict(role=side+"_shoulder_slope",primitive="sphere",export=True,
                              dimensions=[0.90,0.98,length+0.65],location=[0,0,0],
                              segments=20,ring_count=12,frame_mm=slope_frame))
            pad_frame,_=axis_frame(lerp(arm["shoulder"],arm["elbow"],-0.18),
                                   lerp(arm["shoulder"],arm["elbow"],0.30))
            pad=roles[side+"_pauldron"]
            pad.clear()
            pad.update(role=side+"_pauldron",primitive="sphere",export=True,
                       dimensions=[0.98,1.08,1.20],location=[0,0,0],
                       segments=20,ring_count=12,frame_mm=pad_frame)
            shoulder_landmarks[side]=dict(neck=neck,deltoid=deltoid)
        crown=next(a for a in atoms if a["role"]=="helmet_crown")
        head_frame=crown["frame_mm"]
        crown.clear()
        crown.update(role="helmet_crown",primitive="sphere",export=True,
                     dimensions=[1.64,2.00,4.40],location=[0,0.08,7.20],
                     segments=24,ring_count=32,frame_mm=head_frame)
        # The cone begins inside the rounded body. Its shallow tangent-like
        # overlap gives the crown a curved shoulder before narrowing to a tip.
        # Both operands remain hidden; the complete helmet is one export role.
        atoms.extend([
            dict(role="helmet_nape_clip",primitive="cube",export=False,
                 dimensions=[3.5,3.5,4.0],location=[0,0.08,8.60],bevel=0,
                 frame_mm=head_frame),
            dict(role="helmet_tapered_tip",primitive="cone",export=False,
                 radius1=0.492,radius2=0.14,depth=0.65,location=[0,0.08,9.275],
                 scale=[1,2.00/1.64,1],vertices=24,rotation=[0,0,math.pi/24],
                 bevel=0.06,bevel_segments=4,frame_mm=head_frame),
        ])
        p["operations"]=[op for op in p["operations"] if op["target"]!="helmet_crown"]+[
            dict(target="helmet_crown",operand="helmet_nape_clip",operation="INTERSECT",solver="EXACT"),
            dict(target="helmet_crown",operand="helmet_tapered_tip",operation="UNION",solver="EXACT"),
            dict(target="helmet_crown",operand="helmet_face_opening",operation="DIFFERENCE",solver="EXACT"),
        ]
        p.update(adapter_version=7,source_reference=source.reference,
                 source_definition_sha256=source.sha256,
                 torso_anatomy=dict(shape="rounded-ribcage-and-formed-cuirass",shoulder_landmarks=shoulder_landmarks),
                 helmet_top=dict(shape="rounded-body-blended-taper",top_mm=9.60,lower_edge_mm=6.60,
                                 nominal_terminal_width_mm=0.28,rounded_body_width_mm=1.64,
                                 taper_start_mm=8.95),
                 status="revision-7-curved-helmet-organic-torso-review-candidate")
        definitions.append(ComponentDefinition(component_id=source.component_id,version=7,
            name=source.name+" - curved helmet and organic torso",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in atoms if a["export"]),parameters=p))
    return tuple(definitions)
