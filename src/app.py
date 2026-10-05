"""
画像処理API

エンドポイント:
    POST /resize           画像のリサイズ/サムネイル生成
    POST /remove-background 背景の透過化(EC商品写真向け)
    POST /watermark         テキスト透かしの追加
    POST /mask-pii          顔・文字情報のマスキング(個人情報保護)
    POST /classify-document 名刺・領収書等のOCR自動判定(ボーナス機能)

起動:
    uvicorn app:app --reload --port 8000

動作確認:
    http://localhost:8000/docs (Swagger UIが自動生成される)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from processors.pii_mask import mask_pii
from processors.receipt_sort import classify_document
from processors.resize import resize_image
from processors.transparency import remove_background
from processors.watermark import add_text_watermark

app = FastAPI(
    title="画像処理API",
    description="リサイズ・背景透過・透かし・個人情報マスキング・書類OCR自動判定",
    version="1.0.0",
)


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空のファイルです")
    return data


@app.post("/resize", summary="画像のリサイズ/サムネイル生成")
async def resize_endpoint(
    file: UploadFile = File(...),
    max_width: int = 800,
    max_height: int = 800,
    keep_aspect: bool = True,
):
    image_bytes = await _read_upload(file)
    try:
        result = resize_image(image_bytes, max_width, max_height, keep_aspect)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=result, media_type="image/png")


@app.post("/remove-background", summary="背景の透過化(EC商品写真向け)")
async def remove_background_endpoint(
    file: UploadFile = File(...),
    tolerance: int = 20,
):
    image_bytes = await _read_upload(file)
    try:
        result = remove_background(image_bytes, tolerance=tolerance)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=result, media_type="image/png")


@app.post("/watermark", summary="テキスト透かしの追加")
async def watermark_endpoint(
    file: UploadFile = File(...),
    text: str = "SAMPLE",
    position: str = "bottom-right",
    opacity: int = 128,
    font_size: int = 28,
):
    image_bytes = await _read_upload(file)
    try:
        result = add_text_watermark(image_bytes, text, position, opacity, font_size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=result, media_type="image/png")


@app.post("/mask-pii", summary="顔・文字情報のマスキング(個人情報保護)")
async def mask_pii_endpoint(
    file: UploadFile = File(...),
    mask_faces: bool = True,
    mask_text: bool = True,
    method: str = "blur",
):
    image_bytes = await _read_upload(file)
    try:
        result = mask_pii(image_bytes, mask_faces=mask_faces, mask_text=mask_text, method=method)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=result, media_type="image/png")


@app.post("/classify-document", summary="名刺・領収書等のOCR自動判定")
async def classify_document_endpoint(file: UploadFile = File(...)):
    image_bytes = await _read_upload(file)
    try:
        result = classify_document(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return JSONResponse({
        "category": result.category,
        "date": result.date,
        "suggested_filename": result.suggested_filename,
        "raw_text": result.raw_text,
    })


@app.get("/", summary="ヘルスチェック")
async def root():
    return {"status": "ok"}
