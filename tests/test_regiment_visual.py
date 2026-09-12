import pytest

from fdm_sculpt.regiment_validation import assess_build, validate_build


def test_visual_preview_is_rejected_before_manufacturing_checks(tmp_path):
    preview = tmp_path/'preview'
    preview.mkdir()
    (preview/'visual-review.json').write_text('{"digitally_validated": false}')
    with pytest.raises(ValueError, match="visual previews"):
        assess_build(preview)
    with pytest.raises(ValueError, match="visual previews"):
        validate_build(preview, tmp_path/'repeat')
    with pytest.raises(ValueError, match="visual previews"):
        validate_build(tmp_path/'trial', preview)
    assert not (preview/'manifest.json').exists()
