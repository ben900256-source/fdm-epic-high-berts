"""Pin shoulder-hung capes and original seahorse heater shields."""
import json
import math
import os
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V7_DEFINITIONS,ELF_V8_DEFINITIONS,resolve_elf
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition",ELF_V8_DEFINITIONS)
def test_shoulder_cape_revision_preserves_reviewed_anatomy_and_hems(definition):
    instance=ComponentInstanceSpec(definition.component_id,8,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan=resolve_elf(definition,instance)
    previous=next(d for d in ELF_V7_DEFINITIONS if d.component_id==definition.component_id)
    old=resolve_elf(previous,ComponentInstanceSpec(previous.component_id,7,"default",{"sole":TransformSpec()},{"mono":"ivory"}))
    golden=json.loads((ROOT/"tests/fixtures/elf-proof-v8-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"] and component_digest(plan)==golden["plan"]
    assert plan["source_definition_sha256"]==previous.sha256
    assert definition.required_anchors==previous.required_anchors and definition.semantic_slots==previous.semantic_slots
    atoms={a["role"]:a for a in plan["atoms"]}
    assert all(atoms[a["role"]]==a for a in old["atoms"] if a["role"] not in ("cloak","shield","shield_lens_mask","shield_spine"))
    assert "shield_spine" not in atoms and "shield_lens_mask" not in atoms
    assert plan["operations"][2:]==old["operations"][1:]
    assert plan["operations"][:2]==[
        dict(target="shield",operand="shield_left_point_halfspace",operation="INTERSECT",solver="EXACT"),
        dict(target="shield",operand="shield_right_point_halfspace",operation="INTERSECT",solver="EXACT")]
    assert definition.output_roles==tuple(a["role"] for a in plan["atoms"] if a["export"])
    shield=atoms["shield"]
    assert shield["primitive"]=="cube" and shield["dimensions"]==[2.48,1.04,4.55]
    assert plan["shield_height_mm"]/plan["shield_width_mm"]<1.9
    def inside_point_cuts(local):
        world=point(shield["frame_mm"],local)
        for side in ("left","right"):
            matrix=atoms["shield_"+side+"_point_halfspace"]["frame_mm"]
            offset=[world[i]-matrix[i][3] for i in range(3)]
            local_z=sum(matrix[i][2]*offset[i] for i in range(3))
            if local_z<-1e-7:
                return False
        return True
    # Retain the declared 0.28 mm terminal land and the broad upper corners.
    assert all(inside_point_cuts(v) for v in ((-0.42,-1.05,0.90),(-0.14,-1.05,0.90),(-1.51,-1.05,3.1),(0.95,-1.05,3.1)))
    assert not inside_point_cuts((-0.68,-1.05,0.90))
    assert not inside_point_cuts((0.12,-1.05,0.90))
    # Rear stock fills the cavities where the shield meets the arm and brace.
    assert shield["location"][1]+shield["dimensions"][1]/2==pytest.approx(-0.47)
    assert shield["location"][1]-shield["dimensions"][1]/2==pytest.approx(-1.51)
    assert plan["shield_insignia"]["subject"]=="original-seahorse"
    assert plan["shield_insignia"]["minimum_stroke_mm"]>=0.28
    assert plan["shield_insignia"]["nominal_relief_mm"]>=0.25
    for a in (a for a in plan["atoms"] if a["role"].startswith("seahorse_")):
        assert a["primitive"]=="sphere" and a["export"]
        assert a["dimensions"][1]==0.66
    assert len(plan["shield_insignia"]["tail_landmarks"])>=8
    cloak=atoms["cloak"]
    old_cloak=next(a for a in old["atoms"] if a["role"]=="cloak")
    assert cloak["radius1"]==old_cloak["radius1"] and cloak["radius2"]==old_cloak["radius2"]
    assert cloak["location"][2]-cloak["depth"]/2==pytest.approx(old_cloak["location"][2]-old_cloak["depth"]/2)
    assert cloak["depth"]-old_cloak["depth"]==pytest.approx(0.60)
    assert cloak["bevel"]==old_cloak["bevel"] and cloak["bevel_segments"]==4
    for side in ("left","right"):
        attachment=plan["cape_attachments"]["sides"][side]
        drape=atoms["cape_"+side+"_shoulder_drape"]
        assert attachment["crest"][2]>attachment["shoulder"][2]+0.40
        assert attachment["crest_local"][2]>plan["cape_attachments"]["center_top_local_mm"]
        assert drape["primitive"]=="sphere" and drape["frame_mm"]==atoms["torso"]["frame_mm"]
        assert drape["dimensions"]==[0.86,0.90,0.60]
        assert drape["location"][2]-drape["dimensions"][2]/2<plan["cape_attachments"]["center_top_local_mm"]-0.40


def test_revision_eight_spec_and_blender_free_recipe():
    spec=RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v8.json")
    assert [i.version for i in spec.instances]==[8]*5
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    source=(ROOT/"fdm_sculpt/components/elves_v8.py").read_text()
    assert "import bpy" not in source and "blender_backend" not in source


@pytest.mark.integration
def test_saved_shoulder_cape_geometry():
    build=os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a revision-8 review")
    internal=Path(build)/"internal"
    if any(i.version!=8 for i in RegimentSpec.load(internal/"regiment-spec.json").instances):
        pytest.skip("this integration test covers revision 8")
    metrics=json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["self_intersection_count"]==0 and metrics["features"]["passes"]
    assert len(metrics["features"]["cape_shoulders"])==10
    assert all(p["passes"] for p in metrics["features"]["cape_shoulders"])
