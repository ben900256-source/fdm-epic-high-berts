"""Pin domed crowns, rounded sleeve ends and articulated connected grips."""
import json
import math
import os
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V4_DEFINITIONS,ELF_V5_DEFINITIONS,resolve_elf
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition",ELF_V5_DEFINITIONS)
def test_domed_helmet_rolled_armor_and_continuous_articulated_grip(definition):
    instance=ComponentInstanceSpec(definition.component_id,5,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan=resolve_elf(definition,instance)
    previous=next(d for d in ELF_V4_DEFINITIONS if d.component_id==definition.component_id)
    old=resolve_elf(previous,ComponentInstanceSpec(previous.component_id,4,"default",{"sole":TransformSpec()},{"mono":"ivory"}))
    golden=json.loads((ROOT/"tests/fixtures/elf-proof-v5-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"]
    assert component_digest(plan)==golden["plan"]
    assert plan["source_definition_sha256"]==previous.sha256
    assert definition.required_anchors==previous.required_anchors
    assert definition.semantic_slots==previous.semantic_slots
    assert definition.output_roles==previous.output_roles+("right_wrist_bridge",)
    assert plan["operations"]==old["operations"]+[dict(target="helmet_crown",operand="helmet_crown_halfspace",operation="INTERSECT",solver="EXACT")]
    atoms={a["role"]:a for a in plan["atoms"]}
    before={a["role"]:a for a in old["atoms"]}
    for role in ("helmet_rear_shell","helmet_nape_guard","spear","shield","left_forearm"):
        assert atoms[role]==before[role]
    assert atoms["cloak"]==dict(before["cloak"],radius1=before["cloak"]["radius1"]+0.08)
    assert plan["cloak_hem_width_mm"]==pytest.approx(old["cloak_hem_width_mm"]+0.16)
    crown,mask=atoms["helmet_crown"],atoms["helmet_crown_halfspace"]
    assert crown["primitive"]=="sphere" and crown["ring_count"]>=20
    assert crown["location"][2]+crown["dimensions"][2]/2==pytest.approx(9.5)
    assert mask["location"][2]-mask["dimensions"][2]/2==pytest.approx(8.08)
    assert not mask["export"] and crown["frame_mm"]==mask["frame_mm"]
    for side in ("left","right"):
        armor=atoms[side+"_vambrace"]
        assert armor["bevel"]==0.18 and armor["bevel_segments"]==4
        assert armor["radius1"]==0.56 and armor["radius2"]==0.53
        assert armor["depth"]>2*armor["bevel"]
        arm=plan["arms"][side]
        local_elbow=plan["forearm_armor"]["extensions"][side]["elbow_local_z_mm"]
        assert point(armor["frame_mm"],(0,0,local_elbow))==pytest.approx(arm["elbow"],abs=1e-8)
    arm=plan["arms"]["right"]
    assert arm["wrist"]==old["arms"]["right"]["wrist"]
    assert arm["grip"]==old["arms"]["right"]["grip"]
    assert arm["elbow"][0]>old["arms"]["right"]["elbow"][0]+0.07
    assert arm["elbow"][2]>old["arms"]["right"]["elbow"][2]+0.09
    assert atoms["right_upper_arm"]["end"]==atoms["right_forearm"]["start"]==arm["elbow"]
    palm=atoms["right_palm"]
    palm_center=point(palm["frame_mm"],palm["location"])
    assert atoms["right_forearm"]["end"]==pytest.approx(palm_center,abs=1e-8)
    # The bridge center lies on the forearm core axis. Its distal end enters
    # the palm by at least 0.30 mm measured along that axis.
    bridge=atoms["right_wrist_bridge"]
    center=point(bridge["frame_mm"],(0,0,0))
    delta=[b-a for a,b in zip(arm["elbow"],palm_center)]
    norm=math.sqrt(sum(v*v for v in delta))
    fraction=sum((c-e)*d for c,e,d in zip(center,arm["elbow"],delta))/norm**2
    assert 0.7<fraction<0.95
    assert center==pytest.approx([e+fraction*d for e,d in zip(arm["elbow"],delta)],abs=1e-8)
    distance=math.dist(center,palm_center)
    assert bridge["dimensions"][2]/2+min(palm["dimensions"])/2-distance>=0.30
    assert min(bridge["dimensions"][:2])>=0.90
    assert atoms["right_cuff"]["primitive"]=="sphere"
    fingers=atoms["right_grouped_fingers"]
    assert fingers["primitive"]=="cube" and fingers["bevel"]==0.22
    assert fingers["location"][1]-fingers["dimensions"][1]/2 < -1.52


def test_revision_five_spec_is_pinned_and_blender_free():
    spec=RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v5.json")
    assert [i.version for i in spec.instances]==[5]*5
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    source=(ROOT/"fdm_sculpt/components/elves_v5.py").read_text()
    assert "import bpy" not in source and "blender_backend" not in source
    assert len({tuple(d.to_dict()["parameters"]["right_elbow_pose_local_mm"]) for d in ELF_V5_DEFINITIONS})==5


@pytest.mark.integration
def test_saved_rounded_review_geometry():
    build=os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a revision-5 review")
    internal=Path(build)/"internal"
    if any(i.version!=5 for i in RegimentSpec.load(internal/"regiment-spec.json").instances):
        pytest.skip("this integration test covers revision 5")
    metrics=json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["self_intersection_count"]==0 and metrics["features"]["passes"]
    assert len(metrics["features"]["wrist_joins"])==5
    assert len(metrics["features"]["elbow_armor"])==10
    assert len(metrics["features"]["grasps"])==5
    assert all(p["passes"] for p in metrics["features"]["wrist_joins"])
