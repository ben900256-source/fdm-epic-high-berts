import hashlib
import json
from pathlib import Path

import pytest

from fdm_sculpt import viewer


def test_cached_publish_and_failed_update_preserves_current(tmp_path):
    build, cache, destination = (tmp_path/name for name in ('build','cache','viewer'))
    for path in (build, cache, destination/'assets'):
        path.mkdir(parents=True)
    blend = b'baked visual fixture'
    (cache/'part.blend').write_bytes(blend)
    blend_hash = hashlib.sha256(blend).hexdigest()
    record = dict(blend_sha256=blend_hash, definition_sha256='definition', visual_collection='visual')
    (cache/'asset.json').write_text(json.dumps(record))
    (build/'saved-provenance.json').write_text('{"passes":true}')
    job = dict(seed=1001, assembly=dict(assembly_id='unit-one', placements=[]),
        assets={'part@1':dict(directory=str(cache))})
    (build/'assembly-job.json').write_text(json.dumps(job))
    exporter_hash = hashlib.sha256(Path(viewer.__file__).with_name('viewer_export.py').read_bytes()).hexdigest()
    key = hashlib.sha256((blend_hash+exporter_hash).encode()).hexdigest()
    (destination/'assets'/f'{key}.bin').write_bytes(bytes(72))
    (destination/'assets'/f'{key}.json').write_text(json.dumps(dict(pieces=[
        dict(role='left_sole',first_triangle=0,triangle_count=1)])))
    result = viewer.publish(build, destination)
    assert result['exported_parts'] == 0 and result['reused_parts'] == 1
    first_index = json.loads((destination/'reviews.json').read_text())
    first_url = first_index['reviews'][0]['url']
    first_review = destination/first_url.removeprefix('/data/')
    first_bytes = first_review.read_bytes()
    assert json.loads(first_bytes)['assets']['part@1']['pieces'][0]['role']=='left_sole'
    job['assembly']['assembly_id'] = 'unit-two'
    job['assembly']['label'] = 'Center standard'
    (build/'assembly-job.json').write_text(json.dumps(job))
    viewer.publish(build, destination)
    viewer.publish(build, destination)
    index = json.loads((destination/'reviews.json').read_text())
    assert len(index['reviews']) == 2  # Republish replaces a slot, not a duplicate.
    assert index['reviews'][1]['label'] == 'Center standard'
    assert first_review.read_bytes() == first_bytes
    current = (destination/'latest.json').read_bytes()
    catalog_before_failure = (destination/'reviews.json').read_bytes()
    (cache/'part.blend').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='Corrupt'):
        viewer.publish(build, destination)
    assert (destination/'latest.json').read_bytes() == current
    assert (destination/'reviews.json').read_bytes() == catalog_before_failure


def test_bad_piece_ranges_do_not_replace_published_review(tmp_path):
    cache=tmp_path/'cache';build=tmp_path/'build';destination=tmp_path/'viewer'
    for path in (cache,build,destination/'assets'):
        path.mkdir(parents=True)
    payload=b'part fixture'
    digest=hashlib.sha256(payload).hexdigest()
    (cache/'part.blend').write_bytes(payload)
    (cache/'asset.json').write_text(json.dumps(dict(blend_sha256=digest,definition_sha256='definition',visual_collection='visual')))
    (build/'saved-provenance.json').write_text('{"passes":true}')
    (build/'assembly-job.json').write_text(json.dumps(dict(seed=1001,assembly=dict(assembly_id='test'),assets={'part@1':dict(directory=str(cache))})))
    exporter_hash=hashlib.sha256(Path(viewer.__file__).with_name('viewer_export.py').read_bytes()).hexdigest()
    key=hashlib.sha256((digest+exporter_hash).encode()).hexdigest()
    (destination/'assets'/f'{key}.bin').write_bytes(bytes(72))
    (destination/'assets'/f'{key}.json').write_text(json.dumps(dict(pieces=[dict(role='toe',first_triangle=1,triangle_count=1)])))
    (destination/'latest.json').write_text('previous review')
    with pytest.raises(ValueError,match='piece ranges'):
        viewer.publish(build,destination)
    assert (destination/'latest.json').read_text()=='previous review'


def test_server_rejects_directory_traversal():
    handler = object.__new__(viewer.Handler)
    for url in ('/data/../../.env', '/vendor/../../../.env', '/%2e%2e/.env'):
        assert handler.translate_path(url).endswith('nonexistent-viewer-path')


def test_download_rejects_stl_that_does_not_match_review(tmp_path):
    (tmp_path/'viewer-review.json').write_text(json.dumps({'source_stl_sha256': 'wrong'}))
    (tmp_path/'elf-spearman-proof.stl').write_bytes(b'different model')
    with pytest.raises(ValueError, match='does not match'):
        viewer.attach_stl(tmp_path, tmp_path/'published')
    assert not (tmp_path/'published').exists()


def test_workshop_prefers_piece_metadata_over_legacy_review(tmp_path,monkeypatch):
    from fdm_sculpt import workshop
    reviews=tmp_path/'reviews';reviews.mkdir()
    exact=dict(definition_sha256='same',url='exact.bin',pieces=[dict(role='sole',first_triangle=0,triangle_count=1)])
    legacy=dict(definition_sha256='same',url='legacy.bin')
    (reviews/'a.json').write_text(json.dumps(dict(assets={'leg@1':exact})))
    (reviews/'z.json').write_text(json.dumps(dict(assets={'leg@1':legacy})))
    monkeypatch.setattr(workshop,'DATA',tmp_path)
    assembly=dict(placements=[dict(part='leg@1',definition_sha256='same')])
    assert workshop.assets_for(assembly)['leg@1']==exact


def test_locked_spearmen_are_default_and_retired_reviews_cannot_publish(tmp_path):
    policy=viewer.review_defaults()
    assert policy['default_review']=='aurelian-spearmen-organic-faces'
    assert policy['default_review'] not in policy['retired_reviews']
    build=tmp_path/'build';build.mkdir()
    (build/'saved-provenance.json').write_text('{"passes":true}')
    (build/'assembly-job.json').write_text(json.dumps(dict(seed=1001,
        assembly=dict(assembly_id='open-arm-infantry-gallery-trial',placements=[]),assets={})))
    destination=tmp_path/'viewer'
    with pytest.raises(ValueError,match='retired'):
        viewer.publish(build,destination)
    assert not destination.exists()
