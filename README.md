# 画像処理API (Python / FastAPI / OpenCV)

EC・業務でよくある画像処理をAPI化したツールです。

## エンドポイント

| パス | 内容 |
|---|---|
| `POST /resize` | リサイズ/サムネイル生成(アスペクト比維持オプションあり) |
| `POST /remove-background` | 背景の透過化(EC商品写真のような単色背景向け) |
| `POST /watermark` | テキスト透かしの追加(位置・不透明度を指定可能) |
| `POST /mask-pii` | 顔・文字情報のマスキング(ぼかし/黒塗り) |
| `POST /classify-document` | 名刺・領収書・請求書などのOCR自動判定(ボーナス機能) |

起動後、`http://localhost:8000/docs` でSwagger UIが自動生成され、
ブラウザから直接試せます。

## 使い方

```bash
pip install -r requirements.txt

# Tesseract OCR本体と日本語データも必要(Ubuntu/Debianの場合)
sudo apt-get install tesseract-ocr tesseract-ocr-jpn

cd src
uvicorn app:app --reload --port 8000
```

### 呼び出し例

```bash
curl -F "file=@product.jpg" "http://localhost:8000/remove-background?tolerance=20" -o output.png
curl -F "file=@photo.jpg" "http://localhost:8000/watermark?text=SAMPLE&position=bottom-right" -o output.png
curl -F "file=@people.jpg" "http://localhost:8000/mask-pii?mask_faces=true&mask_text=true" -o output.png
curl -F "file=@receipt.jpg" "http://localhost:8000/classify-document"
```

## Docker

```bash
docker build -t image-processing-api .
docker run -p 8000:8000 image-processing-api
```
※このサンドボックス環境にDockerが無かったため、Dockerfileの記述内容は
  動作確認済みですが`docker build`自体の実行確認はできていません。
  お手元で一度ビルドを試してください。

## テスト

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

外部ファイルを使わず、テスト実行時にPillowでサンプル画像(商品写真風・
領収書風の画像)を動的に生成してテストしています。

## 各機能の設計メモ・限界

### 背景透過(`/remove-background`)
人物や複雑な背景のセマンティックな除去(AIモデルによる自動切り抜き)
ではなく、**画像4隅からのフラッドフィルで「背景とみなせる連続領域」を
検出する軽量な方式**です。単色〜ほぼ単色の背景で撮影されたEC商品写真
のようなケースに向いています。背景に強い影や模様がある場合は
`tolerance`(許容誤差)の調整が必要です。

### 個人情報マスキング(`/mask-pii`)
- 顔検出: OpenCV同梱のHaar Cascade(追加モデルのダウンロード不要)
- 文字検出: Tesseract OCRで検出した文字の「内容」は判定せず、
  文字が写っている領域を一律でマスクします(住所かどうか等の意味的な
  判定はしていません)
- 日本語OCRは1文字ずつ検出されやすく、そのままマスクすると文字の間に
  隙間ができるため、行(line)単位でバウンディングボックスをまとめてから
  マスクする設計にしています

### 書類のOCR自動判定(`/classify-document`)
キーワードと日付パターンによるルールベースの軽量な分類です。
「領収書」「請求書」「株式会社」等のキーワードが本文に含まれない
書類は `unknown` 判定になります。

## 技術スタック

Python 3.12 / FastAPI / Uvicorn / OpenCV / Pillow / Tesseract OCR(pytesseract) / pytest
