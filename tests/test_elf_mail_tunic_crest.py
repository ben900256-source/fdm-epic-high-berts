import json
import os
from pathlib import Path

import pytest

from fdm_sculpt.components.core import ComponentInstanceSpec, component_digest
from fdm_sculpt.components.elves import ELF_V10_DEFINITIONS, ELF_V11_DEFINITIONS, resolve_elf
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("definition", ELF_V11_DEFINITIONS)
def test_mail_tunic_crest_resolver_and_golden(definition):
    instance = ComponentInstanceSpec(definition.component_id, 11, "default",
                                     {"sole": TransformSpec()}, {"mono": "ivory"})
    plan = resolve_elf(definition, instance)
    old = next(d for d in ELF_V10_DEFINITIONS if d.component_id == definition.component_id)
    atoms = {a["role"]: a for a in plan["atoms"]}
    old_plan = resolve_elf(old, ComponentInstanceSpec(old.component_id, 10, "default",
                           {"sole": TransformSpec()}, {"mono": "ivory"}))
    for atom in old_plan["atoms"]:
        if atom["role"] not in {"left_pauldron", "right_pauldron"}:
            assert atoms[atom["role"]] == atom
    assert len(plan["mail_panel"]["links_local"]) == 16
    assert all(op["solver"] == "EXACT" for op in plan["operations"])
    golden = json.loads((ROOT/"tests/fixtures/elf-proof-v11-golden.json").read_text())
    assert golden[definition.reference] == dict(definition=definition.sha256, plan=component_digest(plan))


def test_revision_11_spec():
    spec = RegimentSpec.load(ROOT/"specs/elf-spearman-proof-v11.json")
    assert [i.version for i in spec.instances] == [11]*5
    assert RegimentSpec.from_dict(spec.to_dict()) == spec


@pytest.mark.integration
def test_saved_mail_tunic_crest_provenance():
    build = os.environ.get("ELF_PROOF_BUILD")
    if not build:
        pytest.skip("set ELF_PROOF_BUILD to a revision-11 build")
    internal = Path(build)/"internal"
    if any(i.version != 11 for i in RegimentSpec.load(internal/"regiment-spec.json").instances):
        pytest.skip("revision 11 only")
    provenance = json.loads((internal/"saved-provenance.json").read_text())
    assert provenance["passes"] and len(provenance["instances"]) == 5
    hashes = {d.sha256 for d in ELF_V11_DEFINITIONS}
    assert {i["definition_sha256"] for i in provenance["instances"]} == hashes
    if (Path(build)/"visual-review.json").exists():
        assert provenance["checks"]["preview_sources"]
        assert provenance["checks"]["preview_only"]
        assert not (Path(build)/"elf-spearman-proof.stl").exists()
        return
    metrics = json.loads((internal/"mesh-metrics.json").read_text())
    assert metrics["artifact_preflight"]["passes"]
    assert metrics["self_intersection_count"] == 0
