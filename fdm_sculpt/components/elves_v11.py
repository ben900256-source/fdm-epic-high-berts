"""Mail breast panel, cloth sleeves and an attached leaf helmet crest."""
from copy import deepcopy

from .core import ComponentDefinition


def make_definitions(originals):
    definitions = []
    for source in originals:
        if source.version != 10:
            raise ValueError("elf revision 11 derives only from pinned revision 10")
        p = deepcopy(source.to_dict()["parameters"])
        atoms = p["atoms"]
        roles = {a["role"]: a for a in atoms}
        body = p["frames"]["body"]
        head = roles["helmet_crown"]["frame_mm"]
        # A continuous backing carries closed raised links. Recesses are cut
        # into each link before assembly, never through the structural panel.
        atoms.append(dict(role="mail_panel", primitive="cube", export=True,
                          dimensions=[1.92, 0.75, 1.86], location=[0, -0.64, 5.43],
                          bevel=0.16, frame_mm=body))
        links = []
        for row in range(4):
            for column in range(4):
                x = -0.66 + column * 0.44 + (0.04 if row % 2 else -0.04)
                z = 4.80 + row * 0.42
                role = f"mail_link_{row}_{column}"
                atoms.append(dict(role=role, primitive="sphere", export=True,
                                  dimensions=[0.46, 0.66, 0.48], location=[x, -0.97, z],
                                  segments=16, ring_count=12, frame_mm=body))
                atoms.append(dict(role=role+"_recess", primitive="sphere", export=False,
                                  dimensions=[0.20, 0.40, 0.22], location=[x, -1.29, z],
                                  segments=12, ring_count=10, frame_mm=body))
                p["operations"].append(dict(target=role, operand=role+"_recess",
                                             operation="DIFFERENCE", solver="EXACT"))
                links.append([x, -1.30, z])
        sleeves = {}
        for side in ("left", "right"):
            pad = roles[side+"_pauldron"]
            frame = pad["frame_mm"]
            # Retain the stable role identifier, replacing the rounded armor
            # cap with a short flared cloth sleeve in the same posed arm frame.
            pad.clear()
            pad.update(role=side+"_pauldron", primitive="cone", export=True,
                       radius1=0.59, radius2=0.47, depth=1.16,
                       location=[0, 0, 0], vertices=24, bevel=0.12,
                       bevel_segments=3, frame_mm=frame)
            atoms.append(dict(role=side+"_tunic_hem", primitive="cone", export=True,
                              radius1=0.62, radius2=0.59, depth=0.28,
                              location=[0, 0, 0.44], vertices=24, bevel=0.07,
                              bevel_segments=3, frame_mm=frame))
            sleeves[side] = dict(frame_mm=frame, hem_local=[0, 0, 0.44])
        # A broad leaf-shaped heraldic crest sits on the crown's front. Its
        # rounded root is buried in the helmet; no isolated hair-like spikes.
        atoms.append(dict(role="helmet_leaf_crest", primitive="sphere", export=True,
                          dimensions=[0.78, 0.72, 1.44], location=[0, -0.56, 8.64],
                          segments=20, ring_count=20, frame_mm=head))
        atoms.append(dict(role="helmet_crest_spine", primitive="sphere", export=True,
                          dimensions=[0.30, 0.46, 1.20], location=[0, -0.85, 8.62],
                          segments=16, ring_count=16, frame_mm=head))
        p.update(adapter_version=11, source_reference=source.reference,
                 source_definition_sha256=source.sha256,
                 mail_panel=dict(backing_mm=0.75, relief_mm=0.285, links_local=links),
                 tunic_sleeves=sleeves,
                 decorative_crest=dict(shape="raised-leaf-with-central-ridge",
                                       center_local=[0, -0.56, 8.64], frame_mm=head),
                 status="revision-11-mail-tunic-crest-review-candidate")
        definitions.append(ComponentDefinition(
            component_id=source.component_id, version=11,
            name=source.name+" - mail tunic and leaf crest", family=source.family,
            required_anchors=source.required_anchors, semantic_slots=source.semantic_slots,
            output_roles=tuple(a["role"] for a in atoms if a["export"]), parameters=p))
    return tuple(definitions)
