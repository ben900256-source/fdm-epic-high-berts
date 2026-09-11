"""A continuous helmet rim and cheek guards formed by its face aperture."""
from copy import deepcopy

from .core import ComponentDefinition


def make_definitions(originals):
    definitions=[]
    for source in originals:
        if source.version!=8:
            raise ValueError("elf revision 9 derives only from pinned revision 8")
        p=deepcopy(source.to_dict()["parameters"])
        # The crown itself forms the brow and sides. Removing the projecting
        # added plates leaves one outer curvature around the entire opening.
        p["atoms"]=[a for a in p["atoms"] if a["role"] not in ("brow","temple_-1","temple_1")]
        opening=next(a for a in p["atoms"] if a["role"]=="helmet_face_opening")
        opening.update(dimensions=[1.08,2.30,1.96],location=[0,-0.95,7.12],bevel=0.12)
        p.update(adapter_version=9,source_reference=source.reference,
                 source_definition_sha256=source.sha256,
                 helmet_face_frame=dict(shape="continuous-shell-with-rounded-face-aperture",
                                        opening_width_mm=1.08,opening_top_mm=8.10,
                                        corner_rounding_mm=0.12,added_outer_plates=False),
                 status="revision-9-integrated-visor-and-cheek-review-candidate")
        p["helmet_rear_cover"]["face_opening_plane_y_mm"]=0.20
        definitions.append(ComponentDefinition(component_id=source.component_id,version=9,
            name=source.name+" - integrated helmet face rim",family=source.family,
            required_anchors=source.required_anchors,semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in p["atoms"] if a["export"]),parameters=p))
    return tuple(definitions)
