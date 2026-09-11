"""Front-visible swept cape hems, blended elbow bends and pointed crowns."""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .elves_v2 import multiply
from .elves_v3 import axis_frame,lerp


def make_definitions(originals):
    definitions=[]
    for source in originals:
        if source.version!=5:
            raise ValueError("elf revision 6 derives only from pinned revision 5")
        p=deepcopy(source.to_dict()["parameters"])
        atoms=p["atoms"]
        roles={a["role"]:a for a in atoms}
        cloak=roles["cloak"]
        cloak["radius1"]=1.76
        cape_panels={}
        for side,sign in (("left",-1),("right",1)):
            # The hem sweeps forward beside the feet, revealing cloth in a
            # front view instead of increasing only the concealed rear cone.
            hem=[sign*1.20,-0.65,-0.55]
            shoulder=[sign*0.80,0.54,4.65]
            local_frame,depth=axis_frame(hem,shoulder)
            panel_frame=multiply(cloak["frame_mm"],local_frame)
            atoms.append(dict(role="cape_"+side+"_sweep",primitive="cone",export=True,
                              radius1=0.59,radius2=0.28,depth=depth,location=[0,0,0],
                              scale=[1,1.40,1],vertices=24,rotation=[0,0,math.pi/24],
                              bevel=0.16,bevel_segments=4,frame_mm=panel_frame))
            cape_panels[side]=dict(hem=hem,shoulder=shoulder,frame_mm=panel_frame)
            arm=p["arms"][side]
            upper=lerp(arm["elbow"],arm["shoulder"],0.30)
            lower=lerp(arm["elbow"],arm["wrist"],-0.14)
            elbow_frame,length=axis_frame(upper,lower)
            atoms.append(dict(role=side+"_elbow_transition",primitive="sphere",export=True,
                              dimensions=[0.98,1.02,length+0.86],location=[0,0,0],
                              segments=20,ring_count=14,frame_mm=elbow_frame))
        # One continuous tapered nape-to-crown shell, opened at the face.
        removed={"helmet_rear_shell","helmet_rear_halfspace","helmet_nape_guard","helmet_crown_halfspace"}
        atoms[:]=[a for a in atoms if a["role"] not in removed]
        p["operations"]=[op for op in p["operations"] if op["target"] not in ("helmet_rear_shell","helmet_crown")]
        crown=roles["helmet_crown"]
        crown.clear()
        crown.update(role="helmet_crown",primitive="cone",export=True,
                     radius1=0.84,radius2=0.14,depth=3.00,location=[0,0.08,8.10],
                     scale=[1,1.27,1],vertices=24,rotation=[0,0,math.pi/24],
                     bevel=0.08,bevel_segments=4,frame_mm=p["frames"]["head"])
        atoms.extend([
            dict(role="helmet_face_opening",primitive="cube",export=False,
                 dimensions=[3.3,2.0,1.83],location=[0,-1.03,7.185],bevel=0,
                 frame_mm=p["frames"]["head"]),
        ])
        p["operations"].extend([
            dict(target="helmet_crown",operand="helmet_face_opening",operation="DIFFERENCE",solver="EXACT"),
        ])
        p.update(adapter_version=6,source_reference=source.reference,
                 source_definition_sha256=source.sha256,
                 cloak_hem_width_mm=3.52,cape_front_sweeps=cape_panels,
                 helmet_tip_mm=9.60,
                 helmet_top=dict(shape="continuous-nape-to-point-shell",top_mm=9.60,lower_edge_mm=6.60,
                                 nominal_terminal_width_mm=0.28),
                 helmet_rear_cover=dict(face_opening_plane_y_mm=-0.03,roles=["helmet_crown"]),
                 status="revision-6-front-cape-and-elbow-review-candidate")
        definitions.append(ComponentDefinition(component_id=source.component_id,version=6,
            name=source.name+" - swept cape and pointed crown",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in atoms if a["export"]),parameters=p))
    return tuple(definitions)
