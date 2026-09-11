import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.components.core import ComponentInstanceSpec,component_digest
from fdm_sculpt.components.elves import ELF_V9_DEFINITIONS,ELF_V10_DEFINITIONS,resolve_elf
from fdm_sculpt.model import TransformSpec
from fdm_sculpt.regiment_spec import RegimentSpec

ROOT=Path(__file__).resolve().parent.parent


@pytest.mark.parametrize('definition',ELF_V10_DEFINITIONS)
def test_fitted_head_contract_and_preserved_helmet(definition):
    old=next(d for d in ELF_V9_DEFINITIONS if d.component_id==definition.component_id)
    instance=ComponentInstanceSpec(definition.component_id,10,'default',{'sole':TransformSpec()},{'mono':'ivory'})
    plan=resolve_elf(definition,instance)
    atoms={a['role']:a for a in plan['atoms']}
    changed={'cranium','chin','nose_plane'}
    old_plan=resolve_elf(old,ComponentInstanceSpec(old.component_id,9,'default',{'sole':TransformSpec()},{'mono':'ivory'}))
    assert all(atoms[a['role']]==a for a in old_plan['atoms'] if a['role'] not in changed)
    assert atoms['cranium']['dimensions'][0]==1.48
    assert atoms['cranium']['dimensions'][2]==1.88
    assert atoms['nose_plane']['radius1']==0.24 and atoms['nose_plane']['vertices']==4
    assert atoms['head_envelope']['export'] is False
    assert all(o['solver']=='EXACT' for o in plan['operations'])
    assert [o['operation'] for o in plan['operations'] if o['target']=='cranium']==['INTERSECT','UNION','UNION','DIFFERENCE','DIFFERENCE','DIFFERENCE','UNION']
    assert definition.required_anchors==old.required_anchors and definition.semantic_slots==old.semantic_slots
    assert definition.output_roles==tuple(a['role'] for a in plan['atoms'] if a['export'])
    golden=json.loads((ROOT/'tests/fixtures/elf-proof-v10-golden.json').read_text())[definition.reference]
    assert golden==dict(definition=definition.sha256,plan=component_digest(plan))


def test_fitted_head_spec_and_blender_free_recipe():
    spec=RegimentSpec.load(ROOT/'specs/elf-spearman-proof-v10.json')
    assert RegimentSpec.from_dict(spec.to_dict())==spec
    assert [i.version for i in spec.instances]==[10]*5
    text=(ROOT/'fdm_sculpt/components/elves_v10.py').read_text()
    assert 'import bpy' not in text and 'blender_backend' not in text


@pytest.mark.integration
def test_saved_fitted_head_geometry():
    build=os.environ.get('ELF_PROOF_BUILD')
    if not build:
        pytest.skip('set ELF_PROOF_BUILD to a revision-10 proof')
    internal=Path(build)/'internal'
    if any(i.version!=10 for i in RegimentSpec.load(internal/'regiment-spec.json').instances):
        pytest.skip('this integration test covers revision 10')
    metrics=json.loads((internal/'mesh-metrics.json').read_text())
    assert metrics['artifact_preflight']['passes'] and metrics['self_intersection_count']==0
    assert metrics['features']['passes']
    assert len(metrics['features']['fitted_heads'])==5
    assert all(all(h['filled_landmarks']) for h in metrics['features']['fitted_heads'])
