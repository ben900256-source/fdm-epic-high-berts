"""Pin elbow coverage, rounded cloth and the enclosing rear helmet geometry."""
import json
import math
import os
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V3_DEFINITIONS,ELF_V4_DEFINITIONS,resolve_elf
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition",ELF_V4_DEFINITIONS)
def test_guard_extends_over_elbow_with_fixed_wrist_and_unchanged_other_shapes(definition):
    instance=ComponentInstanceSpec(definition.component_id,4,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan=resolve_elf(definition,instance)
    previous=next(d for d in ELF_V3_DEFINITIONS if d.component_id==definition.component_id)
    old=resolve_elf(previous,ComponentInstanceSpec(previous.component_id,3,"default",{"sole":TransformSpec()},{"mono":"ivory"}))
    golden=json.loads((ROOT/"tests/fixtures/elf-proof-v4-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"]
    assert component_digest(plan)==golden["plan"]
    assert plan["source_definition_sha256"]==previous.sha256
    assert definition.output_roles==previous.output_roles+("helmet_rear_shell","helmet_nape_guard")
    assert definition.required_anchors==previous.required_anchors
    assert definition.semantic_slots==previous.semantic_slots
    assert plan["operations"]==old["operations"]+[dict(target="helmet_rear_shell",operand="helmet_rear_halfspace",operation="INTERSECT",solver="EXACT")]
    assert plan["arms"]==old["arms"]
    for atom,before in zip(plan["atoms"],old["atoms"]):
        if atom["role"]=="cloak":
            location=list(before["location"])
            location[2]-=0.25
            assert atom==dict(before,bevel=0.24,bevel_segments=4,depth=before["depth"]+0.50,location=location)
            assert atom["location"][2]+atom["depth"]/2==pytest.approx(before["location"][2]+before["depth"]/2)
            assert atom["location"][2]-atom["depth"]/2+atom["bevel"]<-0.30
            continue
        if atom["role"] not in ("left_vambrace","right_vambrace"):
            assert atom==before
            continue
        side=atom["role"].split("_")[0]
        elbow,wrist=plan["arms"][side]["elbow"],plan["arms"][side]["wrist"]
        delta=[b-a for a,b in zip(elbow,wrist)]
        norm=math.sqrt(sum(v*v for v in delta))
        axis=[v/norm for v in delta]
        start=point(atom["frame_mm"],(0,0,-atom["depth"]/2))
        end=point(atom["frame_mm"],(0,0,atom["depth"]/2))
        previous_end=point(before["frame_mm"],(0,0,before["depth"]/2))
        assert end==pytest.approx(previous_end,abs=1e-8)
        assert start==pytest.approx([e-0.35*v for e,v in zip(elbow,axis)],abs=1e-8)
        assert atom["depth"]>before["depth"]+0.35
        assert atom["radius1"]==0.56 and atom["radius2"]==before["radius2"]
        # The entire 0.94 mm elbow core fits within the sleeve cross-section.
        radius_at_elbow=atom["radius1"]+(atom["radius2"]-atom["radius1"])*0.35/atom["depth"]
        assert radius_at_elbow*math.cos(math.pi/16)>0.47
    atoms={a["role"]:a for a in plan["atoms"]}
    shell,mask=atoms["helmet_rear_shell"],atoms["helmet_rear_halfspace"]
    assert shell["frame_mm"]==mask["frame_mm"]==atoms["cranium"]["frame_mm"]
    assert mask["export"] is False
    assert mask["location"][1]-mask["dimensions"][1]/2==pytest.approx(-0.03)
    # Rear cranium landmarks lie inside the helmet envelope; the front face
    # remains beyond the halfspace, so its reviewed features remain visible.
    skull=atoms["cranium"]
    for row in range(1,12):
        latitude=math.pi*row/12
        for col in range(13):
            longitude=math.pi*col/12
            sample=[skull["location"][0]+skull["dimensions"][0]/2*math.sin(latitude)*math.cos(longitude),
                    skull["location"][1]+skull["dimensions"][1]/2*math.sin(latitude)*math.sin(longitude),
                    skull["location"][2]+skull["dimensions"][2]/2*math.cos(latitude)]
            assert sum(((v-c)/(d/2))**2 for v,c,d in zip(sample,shell["location"],shell["dimensions"]))<1


def test_elbow_spec_is_pinned_and_recipe_is_blender_free():
    spec=RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v4.json")
    assert [i.version for i in spec.instances]==[4]*5
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    source=(ROOT/"fdm_sculpt/components/elves_v4.py").read_text()
    assert "import bpy" not in source and "blender_backend" not in source


@pytest.mark.integration
def test_saved_elbow_review_geometry():
    build=os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a revision-4 review")
    internal=Path(build)/"internal"
    spec=RegimentSpec.load(internal/"regiment-spec.json")
    if any(i.version!=4 for i in spec.instances):
        pytest.skip("this integration test covers revision 4")
    metrics=json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["self_intersection_count"]==0
    assert metrics["features"]["passes"]
    assert len(metrics["features"]["elbow_armor"])==10
    assert len(metrics["features"]["helmet_backs"])==5
    assert all(p["passes"] for p in metrics["features"]["elbow_armor"]+metrics["features"]["grasps"]+metrics["features"]["helmet_backs"])
