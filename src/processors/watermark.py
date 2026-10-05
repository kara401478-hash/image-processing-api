"""画像への透かし(ウォーターマーク)追加"""

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

POSITIONS = ("top-left", "top-right", "bottom-left", "bottom-right", "center")


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    # 環境にある汎用フォントを探す。見つからなければPillow同梱のデフォルトにフォールバック
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def add_text_watermark(image_bytes: bytes, text: str, position: str = "bottom-right",
                        opacity: int = 128, font_size: int = 28,
                        margin: int = 16) -> bytes:
    """
    画像にテキストの透かしを追加する。

    position: top-left / top-right / bottom-left / bottom-right / center
    opacity: 0(完全に透明)〜255(不透明)
    """
    if position not in POSITIONS:
        raise ValueError(f"positionは {POSITIONS} のいずれかにしてください")

    base = Image.open(BytesIO(image_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = _get_font(font_size)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    w, h = base.size
    positions = {
        "top-left": (margin, margin),
        "top-right": (w - text_w - margin, margin),
        "bottom-left": (margin, h - text_h - margin),
        "bottom-right": (w - text_w - margin, h - text_h - margin),
        "center": ((w - text_w) // 2, (h - text_h) // 2),
    }
    xy = positions[position]

    draw.text(xy, text, font=font, fill=(255, 255, 255, opacity))

    combined = Image.alpha_composite(base, overlay)

    out = BytesIO()
    # 元が不透明な形式(jpgなど)だった場合も、透かし付きはPNGで返す
    # (半透明合成した結果をJPEGにすると透明度情報が失われるため)
    combined.save(out, format="PNG")
    return out.getvalue()
