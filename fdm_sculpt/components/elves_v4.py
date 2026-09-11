"""Extended elbow armor, rounded cape edges and an enclosing helmet back."""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .elves_v3 import axis_frame,lerp


ELBOW_OVERLAP_MM = 0.35


def make_definitions(originals):
    definitions=[]
    for source in originals:
        if source.version!=3:
            raise ValueError("elf revision 4 derives only from pinned revision 3")
        p=deepcopy(source.to_dict()["parameters"])
        roles={a["role"]:a for a in p["atoms"]}
        extensions={}
        for side in ("left","right"):
            arm=p["arms"][side]
            elbow,wrist=arm["elbow"],arm["wrist"]
            direction=[b-a for a,b in zip(elbow,wrist)]
            length=math.sqrt(sum(v*v for v in direction))
            start=[round(e-ELBOW_OVERLAP_MM*v/length,9) for e,v in zip(elbow,direction)]
            end=lerp(elbow,wrist,0.97)
            guard_frame,depth=axis_frame(start,end)
            guard=roles[side+"_vambrace"]
            old_depth=guard["depth"]
            guard.update(frame_mm=guard_frame,depth=depth,radius1=0.56)
            extensions[side]=dict(start=start,end=end,elbow=elbow,
                                   extension_mm=round(depth-old_depth,9),
                                   elbow_overlap_mm=ELBOW_OVERLAP_MM,
                                   elbow_local_z_mm=-depth/2+ELBOW_OVERLAP_MM)
        p["forearm_armor"].update(elbow_overlap_mm=ELBOW_OVERLAP_MM,elbow_diameter_mm=1.12,extensions=extensions)
        # Round the cloth's upper perimeter directly, retaining its draped
        # silhouette instead of adding a separate rigid collar or rope.
        roles["cloak"].update(bevel=0.24,bevel_segments=4)
        # Bury the lower bevel inside the strip, keeping the upper edge fixed.
        # This avoids a shallow rounded hem/strip intersection that produces
        # duplicate loop triangles when the Exact result is triangulated.
        roles["cloak"]["depth"]+=0.50
        roles["cloak"]["location"][2]-=0.25
        head_frame=p["frames"]["head"]
        p["atoms"].extend([
            dict(role="helmet_rear_shell",primitive="sphere",export=True,
                 dimensions=[1.42,1.50,2.10],location=[0,0.12,7.50],
                 segments=24,ring_count=12,frame_mm=head_frame),
            dict(role="helmet_rear_halfspace",primitive="cube",export=False,
                 dimensions=[3.0,1.60,3.50],location=[0,0.77,7.50],
                 bevel=0.0,frame_mm=head_frame),
            dict(role="helmet_nape_guard",primitive="cube",export=True,
                 dimensions=[1.20,0.78,0.48],location=[0,0.31,6.75],
                 bevel=0.10,frame_mm=head_frame),
        ])
        p["operations"].append(dict(target="helmet_rear_shell",operand="helmet_rear_halfspace",
                                    operation="INTERSECT",solver="EXACT"))
        p.update(adapter_version=4,source_reference=source.reference,
                 source_definition_sha256=source.sha256,cape_top_rounding_mm=0.24,
                 helmet_rear_cover=dict(face_opening_plane_y_mm=-0.03,back_extent_y_mm=0.87,
                                        roles=["helmet_rear_shell","helmet_nape_guard"]),
                 status="revision-4-armor-and-cloth-review-candidate")
        definitions.append(ComponentDefinition(component_id=source.component_id,version=4,
            name=source.name+" - elbow armor, rounded cloth and helmet back",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in p["atoms"] if a["export"]),parameters=p))
    return tuple(definitions)
