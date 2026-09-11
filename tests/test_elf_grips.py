"""Revision-3 grips must surround the shaft and connect to armored forearms."""
import json
import math
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V2_DEFINITIONS,ELF_V3_DEFINITIONS,resolve_elf
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition",ELF_V3_DEFINITIONS)
def test_wrapped_spear_grips_armored_forearms_and_broader_silhouette(definition):
    instance=ComponentInstanceSpec(definition.component_id,3,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan=resolve_elf(definition,instance)
    golden=json.loads((ROOT/"tests/fixtures/elf-proof-v3-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"]
    assert component_digest(plan)==golden["plan"]
    previous=next(d for d in ELF_V2_DEFINITIONS if d.component_id==definition.component_id)
    old={a["role"]:a for a in previous.to_dict()["parameters"]["atoms"]}
    atoms={a["role"]:a for a in plan["atoms"]}
    assert plan["source_definition_sha256"]==previous.sha256
    assert plan["pose_settings"]==previous.to_dict()["parameters"]["pose_settings"]
    assert definition.required_anchors==("sole",) and definition.semantic_slots==("mono",)
    assert definition.output_roles==tuple(a["role"] for a in plan["atoms"] if a["export"])
    assert plan["operations"]==previous.to_dict()["parameters"]["operations"]
    assert atoms["cloak"]["radius1"]==pytest.approx(old["cloak"]["radius1"]+0.20)
    assert plan["cloak_hem_width_mm"]==pytest.approx(2*atoms["cloak"]["radius1"])
    assert atoms["cloak"]["radius2"]>old["cloak"]["radius2"]
    for role in ("torso","cuirass_lower","cuirass_upper"):
        assert atoms[role]["scale"][0]==pytest.approx(old[role]["scale"][0]*1.10)
    # Palm and fingers both overlap the shaft by real volume in the same
    # rigid frame; front and rear masses extend beyond opposite shaft walls.
    shaft=atoms["spear"]
    palm,fingers=atoms["right_palm"],atoms["right_grouped_fingers"]
    assert all(atoms[r]["frame_mm"]==shaft["frame_mm"] for r in
               ("right_palm","right_grouped_fingers","right_thumb","right_knuckle_plate"))
    for atom,y in ((palm,-0.62),(fingers,-1.0)):
        sample=[1.05,y,plan["spear_grip"]["center"][2]]
        assert abs(y+0.76)<shaft["radius"]-0.15
        if atom["primitive"]=="sphere":
            assert sum(((s-c)/(d/2))**2 for s,c,d in zip(sample,atom["location"],atom["dimensions"]))<1
        else:
            assert all(abs(s-c)<d/2-atom["bevel"] for s,c,d in zip(sample,atom["location"],atom["dimensions"]))
    assert fingers["location"][1]-fingers["dimensions"][1]/2 < -0.76-shaft["radius"]-0.20
    assert palm["location"][1]+palm["dimensions"][1]/2 > -0.76+shaft["radius"]+0.25
    for side in ("left","right"):
        guard=atoms[side+"_vambrace"]
        arm=plan["arms"][side]
        vector=[b-a for a,b in zip(arm["elbow"],arm["wrist"])]
        norm=math.sqrt(sum(v*v for v in vector))
        assert guard["depth"]>0.45
        assert min(guard["radius1"],guard["radius2"])>atoms[side+"_forearm"]["radius"]
        assert [guard["frame_mm"][i][2] for i in range(3)]==pytest.approx([v/norm for v in vector])
        assert atoms[side+"_forearm"]["start"]==pytest.approx(arm["elbow"])
    moved=resolve_elf(definition,ComponentInstanceSpec(definition.component_id,3,"default",
                      {"sole":TransformSpec(translate_mm=(4,0,1))},{"mono":"ivory"}))
    for local,world in zip(plan["atoms"],moved["atoms"]):
        key="location" if "location" in local else "start"
        a=point(local["frame_mm"],local[key]) if "frame_mm" in local else local[key]
        b=point(world["frame_mm"],world[key]) if "frame_mm" in world else world[key]
        assert b==pytest.approx([v+t for v,t in zip(a,(4,0,1))],abs=1e-8)


def test_revision_three_spec_and_blender_free_recipe():
    spec=RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v3.json")
    assert [i.version for i in spec.instances]==[3]*5
    assert [i.component_id[-1] for i in spec.instances]==list("abcde")
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    source=(ROOT/"fdm_sculpt/components/elves_v3.py").read_text()
    assert "import bpy" not in source and "blender_backend" not in source


@pytest.mark.integration
def test_evaluated_revision_three_grasps_and_mesh():
    import os
    build=os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to the generated revision-3 review")
    internal=Path(build)/"internal"
    spec=RegimentSpec.load(internal/"regiment-spec.json")
    if any(i.version!=3 for i in spec.instances):
        pytest.skip("this geometry measurement test covers revision 3")
    metrics=json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["manifold"] and metrics["self_intersection_count"]==0
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["features"]["passes"]
    assert len(metrics["features"]["grasps"])==5
    assert all(g["finger_span_mm"]>=1.30 and g["knuckle_projection_beyond_shaft_mm"]>=0.25
               for g in metrics["features"]["grasps"])
