"""Contract coverage for the five posed revision-2 elf recipes."""
import json
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec, component_digest
from fdm_sculpt.components.elves import ELF_V2_DEFINITIONS, resolve_elf
from fdm_sculpt.components.elves_v2 import point
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT = Path(__file__).resolve().parent.parent


def test_five_distinct_revision_two_poses():
    spec = RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v2.json")
    assert [i.version for i in spec.instances]==[2]*5
    assert [i.component_id[-1] for i in spec.instances]==list("abcde")
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    plans = [resolve_elf(d,ComponentInstanceSpec(d.component_id,2,"default",{"sole":TransformSpec()},{"mono":"ivory"}))
             for d in ELF_V2_DEFINITIONS]
    assert len({p["pose_name"] for p in plans})==5
    assert len({json.dumps(p["legs"],sort_keys=True) for p in plans})==5
    assert len({json.dumps(p["arms"],sort_keys=True) for p in plans})==5
    assert len({json.dumps(p["frames"]["shield"]) for p in plans})==5


@pytest.mark.parametrize("definition",ELF_V2_DEFINITIONS)
def test_larger_shields_flared_hems_and_resolved_frames(definition):
    instance = ComponentInstanceSpec(definition.component_id,2,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan = resolve_elf(definition,instance)
    golden = json.loads((ROOT/"tests/fixtures/elf-proof-v2-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"]
    assert component_digest(plan)==golden["plan"]
    assert plan["source_reference"].endswith("@1")
    assert plan["shield_width_mm"]==2.1
    assert 6.1<plan["shield_height_mm"]<6.2
    assert 2.6<plan["cloak_hem_width_mm"]<2.8
    assert plan["spear_diameter_mm"]>=1
    assert definition.required_anchors==("sole",)
    assert definition.semantic_slots==("mono",)
    assert definition.output_roles==tuple(a["role"] for a in plan["atoms"] if a["export"])
    assert plan["operations"]==[dict(target="shield",operand="shield_lens_mask",operation="INTERSECT",solver="EXACT")]
    moved = resolve_elf(definition,ComponentInstanceSpec(definition.component_id,2,"default",
                        {"sole":TransformSpec(translate_mm=(4,0,1))},{"mono":"ivory"}))
    for before,after in zip(plan["atoms"],moved["atoms"]):
        key = "location" if "location" in before else "start"
        old_point = point(before["frame_mm"],before[key]) if "frame_mm" in before else before[key]
        new_point = point(after["frame_mm"],after[key]) if "frame_mm" in after else after[key]
        assert new_point==pytest.approx([v+t for v,t in zip(old_point,(4,0,1))],abs=1e-8)
    # Segment endpoints must agree with the articulated leg landmarks.
    atoms = {a["role"]:a for a in plan["atoms"]}
    for side in ("left","right"):
        leg = plan["legs"][side]
        assert atoms[side+"_shin"]["start"]==pytest.approx(leg["ankle"],abs=1e-8)
        assert atoms[side+"_shin"]["end"]==pytest.approx(leg["knee"],abs=1e-8)
        assert atoms[side+"_thigh"]["end"]==pytest.approx(leg["hip"],abs=1e-8)
        assert leg["toe"][1]<leg["heel"][1]


def test_pose_recipes_are_blender_free():
    text = (ROOT/"fdm_sculpt/components/elves_v2.py").read_text(encoding="utf-8")
    assert "import bpy" not in text and "blender_backend" not in text
