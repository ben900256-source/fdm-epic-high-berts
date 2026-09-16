from copy import deepcopy

from fdm_sculpt.piece_ids import annotate, lookup


def review():
    return dict(revision='review-one', assembly=dict(assembly_id='spearmen', placements=[
        dict(instance_id=instance, part='leg@5', definition_sha256='hash-five')
        for instance in ('elf-01/leg', 'elf-02/leg')]), assets={
            'leg@5': dict(pieces=[dict(role='toe'), dict(role='sole')])})


def test_ids_survive_revisions_reordering_and_separate_instances(tmp_path):
    source = review()
    before = deepcopy(source)
    initial = annotate(source, tmp_path)['piece_ids']
    assert source == before
    assert len({handle for handles in initial.values() for handle in handles}) == 4
    source['revision'] = 'review-two'
    source['assembly']['placements'].reverse()
    for placement in source['assembly']['placements']:
        placement.update(part='leg@6', definition_sha256='hash-six')
    source['assets'] = {'leg@6': dict(pieces=[dict(role='sole'), dict(role='toe')])}
    updated = annotate(source, tmp_path)['piece_ids']
    for instance, handles in initial.items():
        assert updated[instance] == handles[::-1]
        resolved = lookup('#'+handles[0].lower(), tmp_path)
        assert resolved['instance_id'] == instance
        assert resolved['geometry_role'] == 'toe'
        assert resolved['part'] == 'leg@6'
        assert resolved['revision'] == 'review-two'


def test_distinct_models_duplicate_roles_and_legacy_exports(tmp_path):
    source = review()
    source['assets']['leg@5']['pieces'].append(dict(role='toe'))
    first = annotate(source, tmp_path)['piece_ids']
    assert len(set(first['elf-01/leg'])) == 3
    source['assembly']['assembly_id'] = 'other-model'
    second = annotate(source, tmp_path)['piece_ids']
    assert set(first['elf-01/leg']).isdisjoint(second['elf-01/leg'])
    del source['assets']['leg@5']['pieces']
    legacy = annotate(source, tmp_path)['piece_ids']['elf-01/leg']
    assert len(legacy) == 1
    assert lookup(legacy[0], tmp_path)['geometry_role'] is None
