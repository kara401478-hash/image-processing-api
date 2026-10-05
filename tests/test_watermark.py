import sys
from io import BytesIO
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image

from processors.watermark import add_text_watermark


def test_watermark_preserves_image_size(plain_photo_image):
    result = add_text_watermark(plain_photo_image, "TEST", position="bottom-right")
    original = Image.open(BytesIO(plain_photo_image))
    watermarked = Image.open(BytesIO(result))
    assert watermarked.size == original.size


def test_watermark_changes_pixels(plain_photo_image):
    """透かしを入れた箇所のピクセルが変化していることを確認"""
    result = add_text_watermark(plain_photo_image, "TEST", position="bottom-right", opacity=255)
    original = Image.open(BytesIO(plain_photo_image)).convert("RGBA")
    watermarked = Image.open(BytesIO(result))
    assert original.tobytes() != watermarked.tobytes()


def test_invalid_position_raises():
    with pytest.raises(ValueError):
        add_text_watermark(b"dummy", "TEST", position="middle-ish")
