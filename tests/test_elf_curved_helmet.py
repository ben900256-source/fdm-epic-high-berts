"""Pin rounded tapered helmets and connected torso/shoulder anatomy."""
import json
import math
import os
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V6_DEFINITIONS,ELF_V7_DEFINITIONS,resolve_elf
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition",ELF_V7_DEFINITIONS)
def test_curved_helmet_rounded_chest_and_sloping_shoulders(definition):
    instance=ComponentInstanceSpec(definition.component_id,7,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan=resolve_elf(definition,instance)
    previous=next(d for d in ELF_V6_DEFINITIONS if d.component_id==definition.component_id)
    old=resolve_elf(previous,ComponentInstanceSpec(previous.component_id,6,"default",{"sole":TransformSpec()},{"mono":"ivory"}))
    golden=json.loads((ROOT/"tests/fixtures/elf-proof-v7-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"] and component_digest(plan)==golden["plan"]
    assert plan["source_definition_sha256"]==previous.sha256
    assert definition.required_anchors==previous.required_anchors and definition.semantic_slots==previous.semantic_slots
    assert plan["arms"]==old["arms"] and plan["legs"]==old["legs"] and plan["spear_grip"]==old["spear_grip"]
    atoms={a["role"]:a for a in plan["atoms"]}
    before={a["role"]:a for a in old["atoms"]}
    changed={"helmet_crown","torso","cuirass_lower","cuirass_upper","collar","left_pauldron","right_pauldron"}
    for role,shape in before.items():
        if role not in changed:
            assert atoms[role]==shape
    assert definition.output_roles==previous.output_roles+("left_shoulder_slope","right_shoulder_slope")
    helmet=atoms["helmet_crown"]
    tip=atoms["helmet_tapered_tip"]
    assert helmet["primitive"]=="sphere" and helmet["dimensions"]==[1.64,2.0,4.4]
    assert tip["primitive"]=="cone" and not tip["export"]
    assert tip["radius2"]==0.14 and tip["location"][2]+tip["depth"]/2==pytest.approx(9.6)
    assert not atoms["helmet_nape_clip"]["export"]
    assert plan["helmet_rear_cover"]["roles"]==["helmet_crown"]
    assert plan["operations"]==[old["operations"][0],
        dict(target="helmet_crown",operand="helmet_nape_clip",operation="INTERSECT",solver="EXACT"),
        dict(target="helmet_crown",operand="helmet_tapered_tip",operation="UNION",solver="EXACT"),
        dict(target="helmet_crown",operand="helmet_face_opening",operation="DIFFERENCE",solver="EXACT")]
    # The point is buried inside the rounded body at its root and overlaps
    # the shoulder of the helmet over a meaningful vertical interval.
    for z in (8.97,9.08,9.20):
        x=0.30
        assert sum(((v-c)/(d/2))**2 for v,c,d in zip((x,0.08,z),helmet["location"],helmet["dimensions"]))<1
        t=(z-tip["location"][2]+tip["depth"]/2)/tip["depth"]
        assert x<tip["radius1"]+(tip["radius2"]-tip["radius1"])*t
    # Bury the taper root fully inside the ellipsoid, avoiding a projecting lip.
    root_z=tip["location"][2]-tip["depth"]/2
    body_radius=helmet["dimensions"][0]/2*math.sqrt(1-((root_z-helmet["location"][2])/(helmet["dimensions"][2]/2))**2)
    assert tip["radius1"]<body_radius
    for role in ("torso","cuirass_lower","cuirass_upper","collar"):
        assert atoms[role]["primitive"]=="sphere"
        assert atoms[role]["frame_mm"]==before["torso"]["frame_mm"]
    torso=atoms["torso"]
    def half_width(z):
        return torso["dimensions"][0]/2*math.sqrt(1-((z-torso["location"][2])/(torso["dimensions"][2]/2))**2)
    assert half_width(5.2)>half_width(4.35)+0.25
    for side in ("left","right"):
        marks=plan["torso_anatomy"]["shoulder_landmarks"][side]
        assert marks["neck"][2]>marks["deltoid"][2]+0.20
        slope=atoms[side+"_shoulder_slope"]
        center=point(slope["frame_mm"],(0,0,0))
        assert center==pytest.approx([(a+b)/2 for a,b in zip(marks["neck"],marks["deltoid"])],abs=1e-8)
        assert slope["dimensions"][2]-math.dist(marks["neck"],marks["deltoid"])==pytest.approx(0.65)
        assert min(slope["dimensions"][:2])>=0.90
        assert atoms[side+"_pauldron"]["dimensions"][2]>atoms[side+"_pauldron"]["dimensions"][0]


def test_revision_seven_spec_and_blender_free_recipe():
    spec=RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v7.json")
    assert [i.version for i in spec.instances]==[7]*5
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    source=(ROOT/"fdm_sculpt/components/elves_v7.py").read_text()
    assert "import bpy" not in source and "blender_backend" not in source


@pytest.mark.integration
def test_saved_curved_helmet_and_torso_geometry():
    build=os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a revision-7 review")
    internal=Path(build)/"internal"
    if any(i.version!=7 for i in RegimentSpec.load(internal/"regiment-spec.json").instances):
        pytest.skip("this integration test covers revision 7")
    metrics=json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["self_intersection_count"]==0 and metrics["features"]["passes"]
    assert all(p["passes"] for p in metrics["features"]["helmet_backs"]+metrics["features"]["wrist_joins"])
