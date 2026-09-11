"""Third elf proof: visible closed spear grips, vambraces and broader cloth.

All geometry remains a complete primitive recipe derived from pinned revision
2. Hand coordinates share the spear frame so every posed shaft crosses its fist.
"""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .elves_v2 import point


def lerp(start, end, amount):
    return [round(a+(b-a)*amount,9) for a,b in zip(start,end)]


def axis_frame(start, end):
    """Right-handed rigid frame with local Z along an articulated forearm."""
    delta = [b-a for a,b in zip(start,end)]
    length = math.sqrt(sum(v*v for v in delta))
    if length < 0.1:
        raise ValueError("forearm needs distinct elbow and wrist landmarks")
    z = [v/length for v in delta]
    reference = [1,0,0] if abs(z[0])<0.9 else [0,1,0]
    projection = sum(a*b for a,b in zip(reference,z))
    x = [a-projection*b for a,b in zip(reference,z)]
    norm = math.sqrt(sum(v*v for v in x))
    x = [v/norm for v in x]
    y = [z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]]
    center = lerp(start,end,0.5)
    return [[x[i],y[i],z[i],center[i]] for i in range(3)]+[[0,0,0,1]],length


def make_definitions(originals):
    definitions = []
    for source in originals:
        if source.version != 2:
            raise ValueError("elf revision 3 derives only from pinned revision 2")
        p = deepcopy(source.to_dict()["parameters"])
        atoms = p["atoms"]
        roles = {a["role"]:a for a in atoms}
        body_frame,spear_frame = p["frames"]["body"],p["frames"]["spear"]
        grip_height = p["pose_settings"]["grip"]

        # Broaden the chest in X; deepen its overlap at the buried wrist join.
        for role in ("torso","cuirass_lower","cuirass_upper"):
            roles[role]["scale"][0] = 1.10
            roles[role]["scale"][1] = 0.82
        roles["collar"]["dimensions"][0] = 1.40
        roles["cloak"]["radius1"] += 0.20
        roles["cloak"]["radius2"] = 1.18
        p["cloak_hem_width_mm"] = 2*roles["cloak"]["radius1"]

        # Shaft passes between the palm behind it and grouped fingers in front.
        # The opposing thumb and broad knuckle plate read as one gloved fist.
        roles["right_palm"].update(dimensions=[1.35,1.05,1.10],
            location=[1.05,-0.43,grip_height],frame_mm=spear_frame)
        fingers = roles["right_grouped_fingers"]
        fingers.clear()
        fingers.update(role="right_grouped_fingers",primitive="sphere",export=True,
            dimensions=[1.50,0.90,0.96],location=[1.05,-1.10,grip_height],
            segments=20,ring_count=10,frame_mm=spear_frame)
        roles["right_thumb"].update(dimensions=[0.65,0.70,0.70],
            location=[0.56,-1.03,grip_height+0.22],frame_mm=spear_frame)
        atoms.append(dict(role="right_knuckle_plate",primitive="sphere",export=True,
            dimensions=[1.10,0.38,0.50],location=[1.05,-1.40,grip_height+0.08],
            segments=20,ring_count=10,frame_mm=spear_frame))

        for side,sign in (("left",-1),("right",1)):
            shoulder = point(body_frame,(sign*1.0,0,5.98))
            if side=="right":
                elbow = point(body_frame,(1.0,0.20,grip_height-1.05))
                grip = point(spear_frame,(1.05,-0.76,grip_height))
                wrist = point(spear_frame,(1.05,-0.32,grip_height-0.26))
                core_end = point(spear_frame,(1.05,-0.43,grip_height))
            else:
                elbow = point(body_frame,(-1.0,0.13,p["pose_settings"]["left_grip"]-0.65))
                grip = p["arms"][side]["grip"]
                wrist = lerp(elbow,grip,0.85)
                core_end = grip
            p["arms"][side] = dict(shoulder=shoulder,elbow=elbow,wrist=wrist,grip=grip)
            roles[side+"_pauldron"].update(location=[sign*1.0,0,5.98],frame_mm=body_frame)
            roles[side+"_upper_arm"].update(start=shoulder,end=elbow)
            roles[side+"_elbow"]["location"] = elbow
            roles[side+"_sleeve_root"]["end"] = elbow
            roles[side+"_forearm"].update(start=elbow,end=core_end)
            guard_frame,guard_length = axis_frame(lerp(elbow,wrist,0.03),lerp(elbow,wrist,0.97))
            atoms.append(dict(role=side+"_vambrace",primitive="cone",export=True,
                radius1=0.62,radius2=0.53,depth=guard_length,location=[0,0,0],
                vertices=16,rotation=[0,0,math.pi/16],bevel=0.0,frame_mm=guard_frame))
            cuff_frame,_ = axis_frame(lerp(elbow,wrist,0.75),lerp(elbow,wrist,1.10))
            cuff = roles[side+"_cuff"]
            cuff.update(radius1=0.58,radius2=0.58,depth=0.30,location=[0,0,0],
                        scale=[1,1,1],frame_mm=cuff_frame)

        p.update(adapter_version=3,source_reference=source.reference,
                 source_definition_sha256=source.sha256,torso_width_multiplier=1.10,
                 cape_shoulder_width_mm=2.36,
                 spear_grip=dict(frame_mm=spear_frame,center=[1.05,-0.76,grip_height],
                                 finger_width_mm=1.50,front_projection_mm=0.32,
                                 grammar="palm-grouped-fingers-opposing-thumb-knuckle-plate"),
                 forearm_armor=dict(roles=["left_vambrace","right_vambrace"],
                                    elbow_diameter_mm=1.24,wrist_diameter_mm=1.06),
                 status="revision-3-visual-review-candidate")
        definitions.append(ComponentDefinition(component_id=source.component_id,version=3,
            name=source.name+" - enclosed spear grip",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in atoms if a["export"]),parameters=p))
    return tuple(definitions)
