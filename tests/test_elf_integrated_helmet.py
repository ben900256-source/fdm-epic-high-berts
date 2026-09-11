"""Pin a continuous curved helmet rim around the exposed face."""
import json
import os
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V8_DEFINITIONS,ELF_V9_DEFINITIONS,resolve_elf
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition",ELF_V9_DEFINITIONS)
def test_continuous_helmet_face_rim(definition):
    instance=ComponentInstanceSpec(definition.component_id,9,"default",{"sole":TransformSpec()},{"mono":"ivory"})
    plan=resolve_elf(definition,instance)
    previous=next(d for d in ELF_V8_DEFINITIONS if d.component_id==definition.component_id)
    old=resolve_elf(previous,ComponentInstanceSpec(previous.component_id,8,"default",{"sole":TransformSpec()},{"mono":"ivory"}))
    golden=json.loads((ROOT/"tests/fixtures/elf-proof-v9-golden.json").read_text())[definition.reference]
    assert definition.sha256==golden["definition"] and component_digest(plan)==golden["plan"]
    assert plan["source_definition_sha256"]==previous.sha256
    assert definition.required_anchors==previous.required_anchors and definition.semantic_slots==previous.semantic_slots
    atoms={a["role"]:a for a in plan["atoms"]}
    removed={"brow","temple_-1","temple_1"}
    assert not removed.intersection(atoms)
    assert all(atoms[a["role"]]==a for a in old["atoms"] if a["role"] not in removed|{"helmet_face_opening"})
    assert definition.output_roles==tuple(r for r in previous.output_roles if r not in removed)
    assert plan["operations"]==old["operations"]
    opening=atoms["helmet_face_opening"]
    assert not opening["export"] and opening["primitive"]=="cube"
    assert opening["dimensions"]==[1.08,2.30,1.96]
    assert opening["bevel"]==0.12
    assert opening["location"][2]+opening["dimensions"][2]/2==pytest.approx(8.10)
    assert opening["location"][2]-opening["dimensions"][2]/2<6.60
    assert not plan["helmet_face_frame"]["added_outer_plates"]
    # Leave curved side stock on both sides of the 1.08 mm face opening.
    assert atoms["helmet_crown"]["dimensions"][0]-opening["dimensions"][0]>=0.55


def test_revision_nine_spec_and_blender_free_recipe():
    spec=RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v9.json")
    assert [i.version for i in spec.instances]==[9]*5
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    source=(ROOT/"fdm_sculpt/components/elves_v9.py").read_text()
    assert "import bpy" not in source and "blender_backend" not in source


@pytest.mark.integration
def test_saved_integrated_helmet_geometry():
    build=os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a revision-9 review")
    internal=Path(build)/"internal"
    if any(i.version!=9 for i in RegimentSpec.load(internal/"regiment-spec.json").instances):
        pytest.skip("this integration test covers revision 9")
    metrics=json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["self_intersection_count"]==0 and metrics["features"]["passes"]
    assert len(metrics["features"]["helmet_backs"])==5
    assert len(metrics["features"]["cape_shoulders"])==10
