import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import cv2
import numpy as np

from processors.pii_mask import detect_text_regions, mask_pii


def test_detects_text_regions(japanese_receipt_image):
    arr = np.frombuffer(japanese_receipt_image, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    regions = detect_text_regions(bgr)
    assert len(regions) > 0


def test_masking_darkens_text_area(japanese_receipt_image):
    arr = np.frombuffer(japanese_receipt_image, dtype=np.uint8)
    original_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    masked_bytes = mask_pii(japanese_receipt_image, mask_faces=False, mask_text=True, method="blackbox")
    masked_arr = np.frombuffer(masked_bytes, dtype=np.uint8)
    masked_bgr = cv2.imdecode(masked_arr, cv2.IMREAD_COLOR)

    # 「領収書」の文字があったあたり(左上)が黒くなっているか
    region = masked_bgr[20:50, 20:120]
    assert region.mean() < original_bgr[20:50, 20:120].mean()


def test_no_faces_in_text_only_image(japanese_receipt_image):
    arr = np.frombuffer(japanese_receipt_image, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    from processors.pii_mask import detect_faces
    assert detect_faces(bgr) == []
