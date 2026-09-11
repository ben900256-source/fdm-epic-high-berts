"""Full heads fitted to the helmet envelope, with carved facial landmarks."""
from copy import deepcopy

from .core import ComponentDefinition


def make_definitions(originals):
    definitions=[]
    for source in originals:
        if source.version!=9:
            raise ValueError("elf revision 10 derives only from pinned revision 9")
        p=deepcopy(source.to_dict()["parameters"])
        atoms=p["atoms"]
        roles={a["role"]:a for a in atoms}
        frame=roles["cranium"]["frame_mm"]
        skull=roles["cranium"]
        skull.clear()
        skull.update(role="cranium",primitive="cube",export=True,
                     dimensions=[1.48,1.80,1.88],location=[0,-0.04,7.37],bevel=0.24,frame_mm=frame)
        # A retained primitive envelope keeps the fitted head inside the
        # approved helmet silhouette while filling its brow and temple recess.
        envelope=deepcopy(roles["helmet_crown"])
        envelope.update(role="head_envelope",export=False,dimensions=[1.50,1.76,4.40],segments=28,ring_count=30)
        atoms.append(envelope)
        p["operations"].append(dict(target="cranium",operand="head_envelope",operation="INTERSECT",solver="EXACT"))
        roles["chin"].update(dimensions=[0.94,1.27,0.76],location=[0,-0.05,6.99],bevel=0.22)
        roles["chin"]["export"]=False
        # Preserve the characteristic tapered four-plane nose. Move the same
        # shape forward to retain its relief against the enlarged face.
        roles["nose_plane"]["location"][1]=-0.90
        roles["nose_plane"]["export"]=False
        # A low rounded nose root supports the broad nose tip from below.
        # Its upper surface stays behind the distinctive four-plane nose.
        atoms.append(dict(role="nose_root",primitive="sphere",export=False,
                          dimensions=[0.38,0.52,0.50],location=[0,-0.76,7.10],
                          segments=20,ring_count=16,frame_mm=frame))
        # Fuse the anatomy before carving the face. Subtracting one cutter
        # from overlapping exported solids creates coincident cut surfaces.
        for operand in ("chin","nose_root"):
            p["operations"].append(dict(target="cranium",operand=operand,operation="UNION",solver="EXACT"))
        for side,sign in (("left",-1),("right",1)):
            role=side+"_eye_socket"
            atoms.append(dict(role=role,primitive="cube",export=False,
                              dimensions=[0.44,0.88,0.32],location=[sign*0.31,-0.86,7.72],
                              bevel=0.11,frame_mm=frame))
            p["operations"].append(dict(target="cranium",operand=role,operation="DIFFERENCE",solver="EXACT"))
        atoms.append(dict(role="mouth_line",primitive="cube",export=False,
                          dimensions=[0.64,0.52,0.18],location=[0,-0.72,6.85],bevel=0.055,frame_mm=frame))
        p["operations"].append(dict(target="cranium",operand="mouth_line",operation="DIFFERENCE",solver="EXACT"))
        p["operations"].append(dict(target="cranium",operand="nose_plane",operation="UNION",solver="EXACT"))
        p.update(adapter_version=10,source_reference=source.reference,
                 source_definition_sha256=source.sha256,
                 face_landmarks=dict(head_width_mm=1.48,head_height_mm=1.88,
                     eyes_local=[[-0.31,-0.86,7.72],[0.31,-0.86,7.72]],
                     mouth_local=[0,-0.72,6.85],nose_local=[0,-0.90,7.43],
                     brow_fill_probe_local=[0,-0.60,8.02],temple_fill_probes_local=[[-0.48,-0.38,7.95],[0.48,-0.38,7.95]],
                     grammar="fitted-head-deep-eye-line-long-planar-nose-mouth-and-chin"),
                 status="revision-10-full-head-and-printability-proof-candidate")
        definitions.append(ComponentDefinition(component_id=source.component_id,version=10,
            name=source.name+" - fitted detailed head",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in atoms if a["export"]),parameters=p))
    return tuple(definitions)
