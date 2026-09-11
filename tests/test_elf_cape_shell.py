"""Pin swept cloak panels, continuous helmet shell and elbow transitions."""
import json
import math
import os
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V5_DEFINITIONS,ELF_V6_DEFINITIONS,resolve_elf
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.components.elves_v3 import lerp
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition",ELF_V6_DEFINITIONS)
def test_swept_cape_one_helmet_shell_and_rounded_elbow_overlap(definition):
    instance=ComponentInstanceSpec(definition.component_id,6,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan=resolve_elf(definition,instance)
    previous=next(d for d in ELF_V5_DEFINITIONS if d.component_id==definition.component_id)
    old=resolve_elf(previous,ComponentInstanceSpec(previous.component_id,5,"default",{"sole":TransformSpec()},{"mono":"ivory"}))
    golden=json.loads((ROOT/"tests/fixtures/elf-proof-v6-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"] and component_digest(plan)==golden["plan"]
    assert plan["source_definition_sha256"]==previous.sha256
    assert definition.required_anchors==previous.required_anchors and definition.semantic_slots==previous.semantic_slots
    atoms={a["role"]:a for a in plan["atoms"]}
    before={a["role"]:a for a in old["atoms"]}
    assert definition.output_roles==tuple(a["role"] for a in plan["atoms"] if a["export"])
    assert plan["arms"]==old["arms"] and plan["spear_grip"]==old["spear_grip"]
    for role in ("shield","spear","right_palm","right_grouped_fingers","right_wrist_bridge","left_vambrace","right_vambrace"):
        assert atoms[role]==before[role]
    assert atoms["cloak"]["radius1"]==1.76
    assert atoms["cloak"]["radius2"]==before["cloak"]["radius2"]
    for side,sign in (("left",-1),("right",1)):
        panel=atoms["cape_"+side+"_sweep"]
        ends=plan["cape_front_sweeps"][side]
        assert sign*ends["hem"][0]>sign*ends["shoulder"][0]+0.35
        assert ends["hem"][1]<-0.60 and ends["hem"][2]<-0.50
        assert panel["radius1"]>panel["radius2"]+0.25
        assert panel["bevel"]==0.16 and panel["bevel_segments"]==4
        bridge=atoms[side+"_elbow_transition"]
        assert bridge["primitive"]=="sphere" and min(bridge["dimensions"][:2])>=0.98
        arm=plan["arms"][side]
        upper=lerp(arm["elbow"],arm["shoulder"],0.30)
        lower=lerp(arm["elbow"],arm["wrist"],-0.14)
        center=point(bridge["frame_mm"],(0,0,0))
        assert center==pytest.approx(lerp(upper,lower,0.5),abs=1e-8)
        assert bridge["dimensions"][2]-math.dist(upper,lower)==pytest.approx(0.86)
    assert not ({"helmet_rear_shell","helmet_rear_halfspace","helmet_nape_guard","helmet_crown_halfspace"}&set(atoms))
    helmet=atoms["helmet_crown"]
    opening=atoms["helmet_face_opening"]
    assert not opening["export"]
    assert helmet["primitive"]=="cone"
    assert plan["helmet_rear_cover"]["roles"]==["helmet_crown"]
    assert plan["operations"]==[old["operations"][0],
        dict(target="helmet_crown",operand="helmet_face_opening",operation="DIFFERENCE",solver="EXACT")]
    assert opening["location"][1]+opening["dimensions"][1]/2==pytest.approx(-0.03)
    assert opening["location"][2]+opening["dimensions"][2]/2==pytest.approx(8.10)
    assert helmet["radius2"]==0.14 and helmet["location"][2]+helmet["depth"]/2==pytest.approx(9.6)
    # A continuous rear wall runs from below the cranium to above the brow.
    for z,y in ((6.7,0.70),(7.0,0.76),(7.5,0.82),(8.0,0.60)):
        t=(z-helmet["location"][2]+helmet["depth"]/2)/helmet["depth"]
        radius=helmet["radius1"]+(helmet["radius2"]-helmet["radius1"])*t
        assert (y-helmet["location"][1])/helmet["scale"][1]<radius*math.cos(math.pi/24)


def test_revision_six_spec_and_blender_free_recipe():
    spec=RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v6.json")
    assert [i.version for i in spec.instances]==[6]*5
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    source=(ROOT/"fdm_sculpt/components/elves_v6.py").read_text()
    assert "import bpy" not in source and "blender_backend" not in source


@pytest.mark.integration
def test_saved_cape_shell_geometry():
    build=os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a revision-6 review")
    internal=Path(build)/"internal"
    if any(i.version!=6 for i in RegimentSpec.load(internal/"regiment-spec.json").instances):
        pytest.skip("this integration test covers revision 6")
    metrics=json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["self_intersection_count"]==0 and metrics["features"]["passes"]
    assert len(metrics["features"]["helmet_backs"])==5
    assert len(metrics["features"]["elbow_armor"])==10
    assert all(p["passes"] for p in metrics["features"]["helmet_backs"]+metrics["features"]["wrist_joins"])
