"""
名刺・書類のOCR自動仕分け(ボーナス機能)

スキャン画像からOCRでテキストを抽出し、キーワードと日付パターンから
「領収書」「請求書」「名刺」などの種別を推定し、ファイル名の候補を作る。

あくまで軽量なルールベース分類であり、機械学習による高精度な分類では
ない点に注意(キーワードが本文に含まれていない書類は unknown になる)。
"""

import re
from dataclasses import dataclass

import cv2
import numpy as np
import pytesseract

_DATE_PATTERNS = [
    re.compile(r"(20\d{2})[年/\-](\d{1,2})[月/\-](\d{1,2})"),
]

_CATEGORY_KEYWORDS = {
    "receipt": ["領収書", "領収証", "レシート"],
    "invoice": ["請求書", "御請求書", "お支払い金額"],
    "business_card": ["株式会社", "TEL", "Email", "E-mail", "〒"],
}


@dataclass
class ClassificationResult:
    category: str          # "receipt" / "invoice" / "business_card" / "unknown"
    date: str | None        # "YYYY-MM-DD" 形式。見つからなければNone
    raw_text: str
    suggested_filename: str


def extract_text(image_bytes: bytes) -> str:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("画像の読み込みに失敗しました(未対応の形式か、壊れたファイルです)")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return pytesseract.image_to_string(rgb, lang="jpn+eng")


def _extract_date(text: str) -> str | None:
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            y, mo, d = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


def _classify_category(text: str) -> str:
    scores = {cat: 0 for cat in _CATEGORY_KEYWORDS}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return "unknown"
    return best_cat


_CATEGORY_LABEL_JA = {
    "receipt": "領収書",
    "invoice": "請求書",
    "business_card": "名刺",
    "unknown": "不明",
}


def classify_document(image_bytes: bytes) -> ClassificationResult:
    text = extract_text(image_bytes)
    category = _classify_category(text)
    date = _extract_date(text)

    label = _CATEGORY_LABEL_JA[category]
    filename = f"{label}_{date}.png" if date else f"{label}_日付不明.png"

    return ClassificationResult(category=category, date=date, raw_text=text,
                                 suggested_filename=filename)
