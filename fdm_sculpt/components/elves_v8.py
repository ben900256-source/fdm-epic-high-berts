"""Shoulder-hung cloth and broad pointed shields with seahorse relief."""
from copy import deepcopy
import math

from .core import ComponentDefinition
from .elves_v2 import point,multiply,rotation,translation


def add_shield(p):
    atoms=p["atoms"]
    shield=next(a for a in atoms if a["role"]=="shield")
    shield_frame=shield["frame_mm"]
    atoms[:]=[a for a in atoms if a["role"] not in ("shield_lens_mask","shield_spine")]
    shield.clear()
    shield.update(role="shield",primitive="cube",export=True,
                  dimensions=[2.48,1.04,4.55],location=[-0.28,-0.99,3.175],
                  bevel=0.10,frame_mm=shield_frame)
    cuts=[]
    angle=math.degrees(math.atan(1.95/1.10))
    for side,sign in (("left",-1),("right",1)):
        role="shield_"+side+"_point_halfspace"
        local=multiply(translation([-0.28+sign*0.14,-0.99,0.90]),rotation([0,-sign*angle,0]))
        atoms.append(dict(role=role,primitive="cube",export=False,
                          dimensions=[14,4,14],location=[0,0,7],bevel=0,
                          frame_mm=multiply(shield_frame,local)))
        cuts.append(dict(target="shield",operand=role,operation="INTERSECT",solver="EXACT"))
    p["operations"]=cuts+[op for op in p["operations"] if op["target"]!="shield"]

    def ellipse(role,x,z,width,height):
        atoms.append(dict(role="seahorse_"+role,primitive="sphere",export=True,
                          dimensions=[width,0.66,height],location=[x-0.28,-1.54,z],
                          segments=20,ring_count=12,frame_mm=shield_frame))

    def stroke(role,start,end,width=0.34):
        dx,dz=end[0]-start[0],end[1]-start[1]
        length=math.hypot(dx,dz)
        dx,dz=dx/length,dz/length
        # Keep the relief thickness perpendicular to the shield on every bend.
        local=[[dz,0,dx,(start[0]+end[0])/2-0.28],
               [0,1,0,-1.54],[-dx,0,dz,(start[1]+end[1])/2],[0,0,0,1]]
        atoms.append(dict(role="seahorse_"+role,primitive="sphere",export=True,
                          dimensions=[width,0.66,length+width],location=[0,0,0],
                          segments=16,ring_count=10,frame_mm=multiply(shield_frame,local)))

    ellipse("head",-0.10,4.62,0.52,0.56)
    stroke("snout",(-0.19,4.58),(-0.62,4.58),0.30)
    stroke("crest",(0.01,4.77),(0.07,4.98),0.28)
    neck=[(0.08,4.55),(0.27,4.33),(0.22,4.09),(0.02,3.93)]
    for i,(start,end) in enumerate(zip(neck,neck[1:])):
        stroke("neck_"+str(i),start,end,0.36)
    ellipse("belly",0.12,3.73,0.64,0.95)
    ellipse("back_fin",0.42,3.88,0.42,0.57)
    tail=[(0.20,3.42),(0.43,3.15),(0.56,2.85)]
    tail.extend([(-0.12+0.68*math.cos(math.radians(a)),2.85+0.68*math.sin(math.radians(a)))
                 for a in (-30,-60,-90,-120,-150,-180,-210)])
    for i,(start,end) in enumerate(zip(tail,tail[1:])):
        stroke("tail_"+str(i),start,end,0.30)
    p.update(shield_width_mm=2.48,shield_height_mm=4.55,
             shield_design=dict(shape="broad-shouldered-pointed-heater",top_local_mm=5.45,
                                point_local_mm=0.90,point_flat_width_mm=0.28,
                                center_x_local_mm=-0.28,rear_overlap_extension_mm=0.12),
             shield_insignia=dict(subject="original-seahorse",minimum_stroke_mm=0.28,
                                  nominal_relief_mm=0.36,belly_probe_local=[-0.16,3.73],
                                  field_probe_local=[-1.23,3.73],tail_landmarks=tail))


def make_definitions(originals):
    definitions=[]
    for source in originals:
        if source.version!=7:
            raise ValueError("elf revision 8 derives only from pinned revision 7")
        p=deepcopy(source.to_dict()["parameters"])
        atoms=p["atoms"]
        body_frame=p["frames"]["body"]
        # Raise the continuous cloth itself, keeping its lower plane buried
        # at the same depth in the strip. Rounded gathers sit over the back
        # of each pauldron and merge into this raised upper perimeter.
        cloak=next(a for a in atoms if a["role"]=="cloak")
        cloak["depth"]+=0.60
        cloak["location"][2]+=0.30
        attachments={}
        for side,sign in (("left",-1),("right",1)):
            crest_local=[sign*0.88,0.42,6.50]
            crest=point(body_frame,crest_local)
            atoms.append(dict(role="cape_"+side+"_shoulder_drape",primitive="sphere",export=True,
                              dimensions=[0.86,0.90,0.60],location=[sign*0.88,0.42,6.20],
                              segments=20,ring_count=12,frame_mm=body_frame))
            attachments[side]=dict(crest=crest,crest_local=crest_local,
                                   shoulder=p["arms"][side]["shoulder"])
        add_shield(p)
        p.update(adapter_version=8,source_reference=source.reference,
                 source_definition_sha256=source.sha256,
                 cape_attachments=dict(shape="rounded-cloth-over-shoulders",sides=attachments,
                                       center_top_local_mm=6.375,upper_edge_raise_mm=0.60),
                 status="revision-8-shoulder-cape-seahorse-shield-review-candidate")
        definitions.append(ComponentDefinition(component_id=source.component_id,version=8,
            name=source.name+" - shoulder cape and seahorse shield",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in atoms if a["export"]),parameters=p))
    return tuple(definitions)
