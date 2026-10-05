"""テスト用のサンプル画像を動的に生成するfixture群(外部ファイル不要)"""

from io import BytesIO

import pytest
from PIL import Image, ImageDraw, ImageFont


def _to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def white_bg_circle_image() -> bytes:
    """白背景に青い円(商品写真の簡易モデル)"""
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill=(30, 100, 200))
    return _to_bytes(img)


@pytest.fixture
def plain_photo_image() -> bytes:
    img = Image.new("RGB", (300, 200), (200, 220, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 270, 170], fill=(100, 180, 100))
    return _to_bytes(img)


@pytest.fixture
def japanese_receipt_image() -> bytes:
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 32)
        font_small = ImageFont.truetype(
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 22)
    except OSError:
        font = font_small = ImageFont.load_default()

    img = Image.new("RGB", (500, 320), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "領収書", font=font, fill=(0, 0, 0))
    draw.text((20, 90), "2026年09月30日", font=font_small, fill=(0, 0, 0))
    draw.text((20, 140), "金額: 5,000円", font=font_small, fill=(0, 0, 0))
    draw.text((20, 190), "株式会社テスト商店", font=font_small, fill=(0, 0, 0))
    return _to_bytes(img)
