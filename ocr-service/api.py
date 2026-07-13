"""OCR 推論服務（獨立容器）。用 PaddleOCR 做圖片文字辨識，繁中為主。
與 backend 分離：backend 只透過 HTTP 呼叫本服務（見 DEVELOPMENT-PLAN.md 架構）。
沿用專案慣例：進入點 api.py + 底部 uvicorn.run；容器內固定埠 9001、CMD python api.py。
"""
import io
import os
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image

# PaddleOCR 模型較大，第一次建立會下載模型（容器啟動時做，之後請求就快）。
_OCR = None


def _get_ocr():
    global _OCR
    if _OCR is None:
        from paddleocr import PaddleOCR

        lang = os.getenv("OCR_LANG", "chinese_cht")  # 繁中
        _OCR = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    return _OCR


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_ocr()  # 啟動時預熱、下載模型
    yield


app = FastAPI(title="ocr-service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ocr")
async def do_ocr(file: UploadFile = File(...)):
    """收一張圖片 → 回 {text, lines}。text 為換行拼接的整段文字。"""
    data = await file.read()
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"無法讀取圖片：{e}")

    arr = np.array(img)[:, :, ::-1]  # RGB → BGR（PaddleOCR 內部用 cv2）
    result = _get_ocr().ocr(arr, cls=True)

    lines: list[str] = []
    for page in result or []:
        for line in page or []:
            # line = [box, (text, score)]
            try:
                lines.append(line[1][0])
            except (IndexError, TypeError):
                continue

    return {"text": "\n".join(lines), "lines": lines}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9001)
