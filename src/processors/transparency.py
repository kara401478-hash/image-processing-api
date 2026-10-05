"""
背景の透過化処理。

本格的な人物/物体の背景除去(セマンティックセグメンテーション)には
深層学習モデル(rembg等)が必要だが、今回はEC商品写真のような
「単色〜ほぼ単色の背景で撮影された画像」を主な対象として、
画像4隅からのフラッドフィル(塗りつぶし)で背景領域を検出し、
透過PNGに変換する軽量な方式を採用する。

限界:
    背景に模様や影が強く入っている場合、4隅と地続きでない背景の
    一部が透過されずに残ることがある。その場合は tolerance
    (許容誤差)を上げることである程度対応できる。
"""

from io import BytesIO

import cv2
import numpy as np
from PIL import Image


def remove_background(image_bytes: bytes, tolerance: int = 20) -> bytes:
    """
    画像の背景(4隅から連続した領域とみなせる部分)を透過したPNGを返す。

    tolerance: 背景とみなす色の許容誤差(0-255)。値を上げるほど
               多少色ムラのある背景も透過されやすくなるが、
               被写体まで透過してしまうリスクも上がる。
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("画像の読み込みに失敗しました(未対応の形式か、壊れたファイルです)")

    h, w = bgr.shape[:2]

    # floodFill用のマスクは元画像より上下左右+2pxの余白が必要(OpenCVの仕様)
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)

    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    diff = (tolerance,) * 3

    work = bgr.copy()
    for seed in corners:
        # 既に塗りつぶし済みの場所はスキップ(flood_maskで判定)
        if flood_mask[seed[1] + 1, seed[0] + 1] != 0:
            continue
        cv2.floodFill(
            work, flood_mask, seedPoint=seed, newVal=(0, 0, 0),
            loDiff=diff, upDiff=diff,
            flags=cv2.FLOODFILL_MASK_ONLY | (255 << 8),
        )

    # flood_mask: 背景とみなされた画素が255、それ以外(被写体)が0
    background_mask = flood_mask[1:-1, 1:-1]

    # 背景=透明(alpha=0)、被写体=不透明(alpha=255)
    alpha = np.where(background_mask > 0, 0, 255).astype(np.uint8)

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([rgb, alpha])

    img = Image.fromarray(rgba, mode="RGBA")
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
