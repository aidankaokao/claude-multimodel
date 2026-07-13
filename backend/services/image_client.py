"""文生圖服務的 HTTP client（backend 端）。backend 不自己跑擴散模型，改呼叫獨立的 image 服務。
base_url 走 config（dev=localhost:9003；容器內由 compose 覆寫成 http://image:9003）。
見 DEVELOPMENT-PLAN.md 架構、M4。
"""
import base64

import requests

from config import settings


def generate(prompt: str) -> bytes:
    """把（英文）提示詞送到文生圖服務，回傳 PNG 圖片 bytes。
    timeout 給大（CPU 生圖可能數分鐘）。
    """
    try:
        resp = requests.post(
            f"{settings.image_base_url}/generate",
            json={"prompt": prompt},
            timeout=600,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"文生圖服務呼叫失敗（{settings.image_base_url}）：{e}")
    return resp.content


def img2img(prompt: str, init_image_bytes: bytes, strength: float = 0.5) -> bytes:
    """以既有圖片為起點做 img2img 微調重繪。init image 走 base64 送出，回傳 PNG bytes。"""
    init_b64 = base64.b64encode(init_image_bytes).decode()
    try:
        resp = requests.post(
            f"{settings.image_base_url}/img2img",
            json={"prompt": prompt, "init_image": init_b64, "strength": strength},
            timeout=600,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"文生圖服務(img2img)呼叫失敗（{settings.image_base_url}）：{e}")
    return resp.content
