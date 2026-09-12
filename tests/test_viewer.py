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
    (build/'assembly-job.json').write_text(json.dumps(dict(seed=1001, assembly=dict(placements=[]),
        assets={'part@1':dict(directory=str(cache))})))
    exporter_hash = hashlib.sha256(Path(viewer.__file__).with_name('viewer_export.py').read_bytes()).hexdigest()
    key = hashlib.sha256((blend_hash+exporter_hash).encode()).hexdigest()
    (destination/'assets'/f'{key}.bin').write_bytes(bytes(72))
    result = viewer.publish(build, destination)
    assert result['exported_parts'] == 0 and result['reused_parts'] == 1
    current = (destination/'latest.json').read_bytes()
    (cache/'part.blend').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='Corrupt'):
        viewer.publish(build, destination)
    assert (destination/'latest.json').read_bytes() == current


def test_server_rejects_directory_traversal():
    handler = object.__new__(viewer.Handler)
    for url in ('/data/../../.env', '/vendor/../../../.env', '/%2e%2e/.env'):
        assert handler.translate_path(url).endswith('nonexistent-viewer-path')
