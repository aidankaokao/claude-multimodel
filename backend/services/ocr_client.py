"""OCR 服務的 HTTP client（backend 端）。backend 不自己跑 OCR，改呼叫獨立的 ocr 服務。
base_url 走 config（dev=localhost:9001；容器內由 compose 覆寫成 http://ocr:9001）。
見 DEVELOPMENT-PLAN.md 架構、M2。
"""
import requests

from config import settings


def recognize(image_bytes: bytes, filename: str = "upload.png") -> str:
    """把圖片送到 OCR 服務，回傳辨識出的整段文字（換行拼接）。"""
    try:
        resp = requests.post(
            f"{settings.ocr_base_url}/ocr",
            files={"file": (filename, image_bytes)},
            timeout=120,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"OCR 服務呼叫失敗（{settings.ocr_base_url}）：{e}")
    return resp.json().get("text", "")
