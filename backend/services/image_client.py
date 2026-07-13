"""文生圖服務的 HTTP client（backend 端）。backend 不自己跑擴散模型，改呼叫獨立的 image 服務。
base_url 走 config（dev=localhost:9003；容器內由 compose 覆寫成 http://image:9003）。
見 DEVELOPMENT-PLAN.md 架構、M4。
"""
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
