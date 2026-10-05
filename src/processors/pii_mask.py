"""
個人情報マスキング処理。

写真に写り込んだ「顔」と「文字情報(住所・電話番号・氏名など)」を検出し、
ぼかし or 黒塗りで隠す。

- 顔検出: OpenCV同梱のHaar Cascade(学習済みモデル。追加ダウンロード不要)
- 文字検出: Tesseract OCR(pytesseract)で文字領域の座標を取得
           ※文字の「内容」までは判定せず、文字が検出された領域を
             一律でマスクする設計(内容を解釈して「ここは住所だから隠す」
             といった判定はしていない点に注意)
"""

from dataclasses import dataclass
from io import BytesIO

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pytesseract import Output

_FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_face_cascade = cv2.CascadeClassifier(_FACE_CASCADE_PATH)


@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int
    kind: str  # "face" or "text"


def detect_faces(bgr: np.ndarray) -> list[Region]:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return [Region(x=int(x), y=int(y), w=int(w), h=int(h), kind="face") for (x, y, w, h) in faces]


def detect_text_regions(bgr: np.ndarray, min_confidence: int = 40, padding: int = 4) -> list[Region]:
    """
    文字領域を検出し、行(line)単位でまとめたバウンディングボックスを返す。

    pytesseractは特に日本語の場合、単語(word)単位の検出が文字1〜2文字
    ごとに細切れになりやすく、そのままマスクすると文字の間に隙間が
    残ってしまう。そのため block_num/par_num/line_num が同じ検出結果を
    1行としてまとめ、その行全体を1つの矩形としてマスクする。
    """
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    data = pytesseract.image_to_data(rgb, lang="jpn+eng", output_type=Output.DICT)

    lines: dict[tuple, list[int]] = {}
    for i, text in enumerate(data["text"]):
        if not text.strip():
            continue
        try:
            conf = int(float(data["conf"][i]))
        except (ValueError, TypeError):
            continue
        if conf < min_confidence:
            continue

        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(i)

    regions = []
    for indices in lines.values():
        xs1 = [data["left"][i] for i in indices]
        ys1 = [data["top"][i] for i in indices]
        xs2 = [data["left"][i] + data["width"][i] for i in indices]
        ys2 = [data["top"][i] + data["height"][i] for i in indices]

        x1, y1 = min(xs1) - padding, min(ys1) - padding
        x2, y2 = max(xs2) + padding, max(ys2) + padding

        regions.append(Region(x=x1, y=y1, w=x2 - x1, h=y2 - y1, kind="text"))

    return regions


def _apply_mask(bgr: np.ndarray, region: Region, method: str, blur_strength: int) -> None:
    x, y, w, h = region.x, region.y, region.w, region.h
    x, y = max(x, 0), max(y, 0)
    w = min(w, bgr.shape[1] - x)
    h = min(h, bgr.shape[0] - y)
    if w <= 0 or h <= 0:
        return

    roi = bgr[y:y + h, x:x + w]
    if method == "blackbox":
        bgr[y:y + h, x:x + w] = 0
    else:  # blur
        k = max(3, blur_strength | 1)  # 奇数にする
        bgr[y:y + h, x:x + w] = cv2.GaussianBlur(roi, (k, k), 0)


def mask_pii(image_bytes: bytes, mask_faces: bool = True, mask_text: bool = True,
             method: str = "blur", blur_strength: int = 35,
             min_text_confidence: int = 40) -> bytes:
    """
    画像中の顔・文字情報をマスクする。

    method: "blur"(ぼかし) か "blackbox"(黒塗り)
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("画像の読み込みに失敗しました(未対応の形式か、壊れたファイルです)")

    regions: list[Region] = []
    if mask_faces:
        regions.extend(detect_faces(bgr))
    if mask_text:
        regions.extend(detect_text_regions(bgr, min_confidence=min_text_confidence))

    for region in regions:
        _apply_mask(bgr, region, method=method, blur_strength=blur_strength)

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
