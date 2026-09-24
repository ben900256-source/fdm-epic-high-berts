import json
import os
from pathlib import Path
import pytest
from fdm_sculpt.modular_print import build, compare, check_union_coverage, restore_model_coordinates, cached_figure_translations
from fdm_sculpt.components.print_trial import trial_mail_skirt, spaced_trial_mail_skirt, trial_equipment_brace
from fdm_sculpt.components.parts import catalog, resolve_assembly
from fdm_sculpt.components.mail_internal_fill import mail_internal_fill, spearman_join_fill


def test_union_cannot_silently_lose_its_backing():
    original = dict(volume_mm3=17.267742, bounds_min_mm=[-2,-2,-4.885], bounds_max_mm=[2,2,-.5])
    check_union_coverage(dict(original, volume_mm3=17.274072), [original])
    with pytest.raises(ValueError, match='volume'):
        check_union_coverage(dict(original, volume_mm3=.001859), [original])
    with pytest.raises(ValueError, match='extent'):
        check_union_coverage(dict(original, bounds_min_mm=[-2,-2,-4.555]), [original])


def test_slicer_center_is_undone_for_shield_overhang():
    from fdm_sculpt.formats import Mesh
    mesh = Mesh(((-10,-3,0),(10,2.5,0),(0,0,10)), ((0,1,2),))
    layers = [dict(z=.14, paths=[(0,0,1,1,.25,'External perimeter')])]
    assert restore_model_coordinates(layers, mesh) == [0,-.25]
    assert layers[0]['paths'] == [(0,-.25,1,.75,.25,'External perimeter')]


def test_cached_seating_moves_complete_figures_and_rejects_pose_changes():
    previous = dict(placements=[dict(instance_id=f'elf-{i+1:02}/{slot}', part=slot+'@1',
        definition_sha256=slot, mount=[[1,0,0,-8+4*i],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
        for i in range(5) for slot in ('torso','spear')])
    current = json.loads(json.dumps(previous))
    for p in current['placements']:
        if p['instance_id'].startswith('elf-'):
            p['mount'][2][3] += .01
    translations = cached_figure_translations(previous, current)
    for index, actual in enumerate(translations):
        assert actual == pytest.approx([4*index,0,.01])
    for p in current['placements']:
        if p['instance_id'].startswith('elf-04/'):
            p['mount'][2][3] += .005
    assert cached_figure_translations(previous, current)[3] == pytest.approx([12,0,.015])
    spear = next(p for p in current['placements'] if p['instance_id']=='elf-03/spear')
    spear['mount'][2][3] += .001
    with pytest.raises(ValueError, match='alignment'):
        cached_figure_translations(previous, current)
    current['placements'].remove(spear)
    with pytest.raises(ValueError, match='every pinned part'):
        cached_figure_translations(previous, current)


def test_trial_skirt_recipe_golden_and_outward_open_recesses():
    root = Path(__file__).resolve().parent.parent
    definitions = catalog()
    part = spaced_trial_mail_skirt(definitions, seed=1001)
    golden = json.loads((root/'tests/fixtures/spearman-print-trial-golden.json').read_text())
    assert part.sha256 == golden[part.reference] == definitions[part.reference].sha256
    assert spaced_trial_mail_skirt(definitions, seed=1001).sha256 == part.sha256
    prior = trial_mail_skirt(definitions, seed=1001)
    assert prior.sha256 == golden[prior.reference]
    parameters = part.to_dict()['parameters']
    assert parameters['print_trial']['source_sha256'] == definitions['aurelian.skirt@3'].sha256
    for atom in parameters['atoms']:
        if atom['role'].endswith('_eye'):
            # The cut stays outward of the link center, away from its backing.
            assert atom['location'][1]-atom['dimensions'][1]/2 >= .099
            assert atom['location'][1]+atom['dimensions'][1]/2 > .21


@pytest.mark.parametrize('seed', [True, 1002, None])
def test_review_seed_must_match_before_launch(tmp_path, seed):
    review = tmp_path/'review'
    review.mkdir()
    (review/'assembly-job.json').write_text(json.dumps({'seed':1001}))
    with pytest.raises(ValueError, match='integer seed'):
        build(review, tmp_path/'trial', seed=seed)
    assert not (tmp_path/'trial').exists()


def test_never_overwrite_a_trial(tmp_path):
    (tmp_path/'assembly-job.json').write_text(json.dumps({'seed':1001}))
    with pytest.raises(ValueError, match='fresh output'):
        build(tmp_path, tmp_path, seed=1001)


def test_comparison_requires_independence_and_detects_changed_geometry(tmp_path):
    left, right = tmp_path/'a', tmp_path/'b'
    with pytest.raises(ValueError, match='independent'):
        compare(left, left)
    for folder in (left, right):
        (folder/'internal').mkdir(parents=True)
        (folder/'internal/mesh-metrics.json').write_text(json.dumps({'seed':1001,'mesh_hash':'a'}))
        (folder/'internal/assembly-job.json').write_text(json.dumps({'seed':1001,'assembly':{'id':'test'}}))
        (folder/'internal/exact-union-order.json').write_text('["a", "b"]')
        (folder/'elf-spearman-proof.stl').write_bytes(b'identical test artifact')
    assert compare(left, right)['passes']
    (right/'elf-spearman-proof.stl').write_bytes(b'changed test artifact')
    result = compare(left, right)
    assert not result['passes']
    assert not result['checks']['stl']


def test_trial_viewer_uses_exported_coordinates_and_stl_hash(tmp_path, monkeypatch):
    import array
    from fdm_sculpt import formats, viewer
    from fdm_sculpt.modular_print import publish
    from fdm_sculpt.atelier import file_hash
    output, data = tmp_path/'trial', tmp_path/'viewer'
    (output/'internal').mkdir(parents=True)
    (output/'internal/assembly-job.json').write_text(json.dumps({'seed':1001}))
    (output/'internal/exact-union-order.json').write_text('["part"]')
    mesh = formats.Mesh(((1,2,3),(2,2,3),(1,3,3)), ((0,1,2),))
    formats.write_binary_stl(output/'elf-spearman-proof.stl', mesh)
    monkeypatch.setattr(viewer, 'DATA', data)
    revision = publish(output)
    manifest = json.loads((data/'latest.json').read_text())
    assert manifest['revision'] == revision
    assert manifest['source_stl_sha256'] == file_hash(output/'elf-spearman-proof.stl')
    asset, = manifest['assets'].values()
    values = array.array('f')
    values.frombytes((data/'assets'/asset['url'].split('/')[-1]).read_bytes())
    assert list(values[:6]) == [1,2,3,0,0,1]
    assert manifest['visual_only'] is True


@pytest.mark.integration
def test_saved_modular_trial_artifacts():
    folder = os.environ.get('MODULAR_PRINT_PROOF')
    if not folder:
        pytest.skip('set MODULAR_PRINT_PROOF to an exported manufacturing trial')
    output = Path(folder)
    record = json.loads((output/'modular-print.json').read_text())
    assert record['removed_triangles'] == 0
    assert record['topology']['watertight']
    assert record['topology']['manifold']
    assert record['topology']['outward_facing']
    assert record['topology']['connected_components'] == 1
    assert json.loads((output/'internal/manufacturing-provenance.json').read_text())['passes']
    assert json.loads((output/'geometry-comparison.json').read_text())['passes']
    assert record['digitally_validated'] is False
