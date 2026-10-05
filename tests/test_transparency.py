import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image

from processors.transparency import remove_background


def test_corners_become_transparent(white_bg_circle_image):
    result = remove_background(white_bg_circle_image, tolerance=20)
    img = Image.open(BytesIO(result))
    assert img.mode == "RGBA"
    assert img.getpixel((1, 1))[3] == 0  # 左上の角は透明


def test_subject_stays_opaque(white_bg_circle_image):
    result = remove_background(white_bg_circle_image, tolerance=20)
    img = Image.open(BytesIO(result))
    center = img.width // 2, img.height // 2
    assert img.getpixel(center)[3] == 255  # 中心の円は不透明のまま
