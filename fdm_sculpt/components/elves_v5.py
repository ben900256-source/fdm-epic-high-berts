"""Domed crowns, rolled armor ends and continuous wrist-to-grip transitions."""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .elves_v2 import point
from .elves_v3 import axis_frame,lerp


RIGHT_ELBOW_LOCAL={
    "a":(1.14,0.30,-0.94),
    "b":(1.28,0.38,-0.75),
    "c":(1.08,0.18,-0.93),
    "d":(1.30,0.45,-0.73),
    "e":(1.30,0.27,-0.82),
}


def make_definitions(originals):
    definitions=[]
    for source in originals:
        if source.version!=4:
            raise ValueError("elf revision 5 derives only from pinned revision 4")
        p=deepcopy(source.to_dict()["parameters"])
        atoms=p["atoms"]
        roles={a["role"]:a for a in atoms}
        head_frame,spear_frame=p["frames"]["head"],p["frames"]["spear"]
        roles["cloak"]["radius1"]+=0.08
        p["cloak_hem_width_mm"]=2*roles["cloak"]["radius1"]
        p["cape_additional_hem_flare_mm"]=0.16
        grip_z=p["spear_grip"]["center"][2]
        # Lift and splay actual elbow landmarks in five restrained variations.
        # Wrist and grip positions remain fixed on their posed spear shafts.
        arm=p["arms"]["right"]
        ex,ey,ez=RIGHT_ELBOW_LOCAL[source.component_id[-1]]
        elbow=point(p["frames"]["body"],(ex,ey,grip_z+ez))
        arm["elbow"]=elbow
        roles["right_upper_arm"]["end"]=elbow
        roles["right_elbow"]["location"]=elbow
        roles["right_sleeve_root"]["end"]=elbow
        roles["right_forearm"]["start"]=elbow
        delta=[b-a for a,b in zip(elbow,arm["wrist"])]
        length=math.sqrt(sum(v*v for v in delta))
        start=[round(e-0.35*v/length,9) for e,v in zip(elbow,delta)]
        end=lerp(elbow,arm["wrist"],0.97)
        guard_frame,depth=axis_frame(start,end)
        old_depth=roles["right_vambrace"]["depth"]
        roles["right_vambrace"].update(frame_mm=guard_frame,depth=depth)
        p["forearm_armor"]["extensions"]["right"].update(start=start,end=end,elbow=elbow,
            extension_mm=round(depth-old_depth,9),elbow_local_z_mm=-depth/2+0.35)
        roles["right_cuff"]["frame_mm"],_=axis_frame(lerp(elbow,arm["wrist"],0.75),lerp(elbow,arm["wrist"],1.10))
        crown=roles["helmet_crown"]
        crown.clear()
        crown.update(role="helmet_crown",primitive="sphere",export=True,
                     dimensions=[1.44,1.30,2.72],location=[0,0.05,8.14],
                     segments=24,ring_count=20,frame_mm=head_frame)
        atoms.append(dict(role="helmet_crown_halfspace",primitive="cube",export=False,
                          dimensions=[3,3,4],location=[0,0.05,10.08],bevel=0,
                          frame_mm=head_frame))
        p["operations"].append(dict(target="helmet_crown",operand="helmet_crown_halfspace",
                                    operation="INTERSECT",solver="EXACT"))
        for side in ("left","right"):
            roles[side+"_vambrace"].update(bevel=0.18,bevel_segments=4,
                                         vertices=24,rotation=[0,0,math.pi/24])
            roles[side+"_cuff"].update(bevel=0.12,bevel_segments=4)

        # Fuller palm/heel runs back into the wrist; the grouped fingers stay
        # on the front of the shaft with one opposing, overlapping thumb.
        palm=roles["right_palm"]
        palm.update(dimensions=[1.30,1.24,1.24],location=[1.05,-0.49,grip_z-0.07],
                    segments=20,ring_count=12)
        fingers=roles["right_grouped_fingers"]
        fingers.clear()
        fingers.update(role="right_grouped_fingers",primitive="cube",export=True,
                       dimensions=[1.46,0.92,1.04],location=[1.05,-1.10,grip_z],
                       bevel=0.22,frame_mm=spear_frame)
        roles["right_thumb"].update(dimensions=[0.62,0.66,0.76],
                                    location=[0.52,-1.08,grip_z+0.16],segments=20,ring_count=12)
        roles["right_knuckle_plate"].update(dimensions=[1.18,0.38,0.62],
                                            location=[1.05,-1.39,grip_z+0.07])
        palm_center=point(spear_frame,palm["location"])
        roles["right_forearm"]["end"]=palm_center
        wrist_frame,_=axis_frame(lerp(arm["elbow"],palm_center,0.62),palm_center)
        atoms.append(dict(role="right_wrist_bridge",primitive="sphere",export=True,
                          dimensions=[1.02,0.98,1.10],location=[0,0,0],
                          segments=20,ring_count=12,frame_mm=wrist_frame))
        cuff=roles["right_cuff"]
        cuff_frame=cuff["frame_mm"]
        cuff.clear()
        cuff.update(role="right_cuff",primitive="sphere",export=True,
                    dimensions=[1.12,1.08,0.72],location=[0,0,0],
                    segments=20,ring_count=12,frame_mm=cuff_frame)
        p["spear_grip"].update(finger_width_mm=1.46,front_projection_mm=0.30,
                               wrist_bridge_frame_mm=wrist_frame,
                               grammar="rounded-palm-grouped-fingers-thumb-knuckle-plate-continuous-wrist")
        p["forearm_armor"].update(end_rounding_mm=0.18,end_rounding_segments=4)
        p.update(adapter_version=5,source_reference=source.reference,
                 source_definition_sha256=source.sha256,
                 right_elbow_pose_local_mm=[ex,ey,grip_z+ez],
                 helmet_top=dict(shape="upper-ellipsoid",top_mm=9.5,lower_clip_mm=8.08),
                 status="revision-5-rounded-armor-and-connected-grip-review-candidate")
        definitions.append(ComponentDefinition(component_id=source.component_id,version=5,
            name=source.name+" - domed crown and connected gauntlet",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in atoms if a["export"]),parameters=p))
    return tuple(definitions)
