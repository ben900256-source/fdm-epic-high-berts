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
    result = viewer.publish(build, destination)
    assert result['exported_parts'] == 0 and result['reused_parts'] == 1
    first_index = json.loads((destination/'reviews.json').read_text())
    first_url = first_index['reviews'][0]['url']
    first_review = destination/first_url.removeprefix('/data/')
    first_bytes = first_review.read_bytes()
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


def test_server_rejects_directory_traversal():
    handler = object.__new__(viewer.Handler)
    for url in ('/data/../../.env', '/vendor/../../../.env', '/%2e%2e/.env'):
        assert handler.translate_path(url).endswith('nonexistent-viewer-path')
