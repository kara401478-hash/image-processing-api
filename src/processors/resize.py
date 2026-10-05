"""画像のリサイズ・サムネイル生成"""

from io import BytesIO

from PIL import Image


def resize_image(image_bytes: bytes, max_width: int, max_height: int,
                  keep_aspect: bool = True) -> bytes:
    """
    画像を指定サイズ以内にリサイズする。
    keep_aspect=True の場合、アスペクト比を保ったまま
    max_width x max_height に収まる最大サイズにする(contain方式)。
    """
    img = Image.open(BytesIO(image_bytes))
    original_format = img.format or "PNG"

    if keep_aspect:
        img.thumbnail((max_width, max_height), Image.LANCZOS)
    else:
        img = img.resize((max_width, max_height), Image.LANCZOS)

    out = BytesIO()
    img.save(out, format=original_format)
    return out.getvalue()
