import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processors.receipt_sort import classify_document


def test_classifies_receipt_and_extracts_date(japanese_receipt_image):
    result = classify_document(japanese_receipt_image)
    assert result.category == "receipt"
    assert result.date == "2026-09-30"
    assert "領収書" in result.suggested_filename
