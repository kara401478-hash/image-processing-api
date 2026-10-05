import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image

from processors.resize import resize_image


def test_resize_keeps_aspect_ratio(white_bg_circle_image):
    result = resize_image(white_bg_circle_image, max_width=100, max_height=50, keep_aspect=True)
    img = Image.open(BytesIO(result))
    assert img.width <= 100
    assert img.height <= 50


def test_resize_without_aspect_forces_exact_size(white_bg_circle_image):
    result = resize_image(white_bg_circle_image, max_width=80, max_height=120, keep_aspect=False)
    img = Image.open(BytesIO(result))
    assert img.size == (80, 120)
