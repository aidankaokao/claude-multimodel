"""TTS 服務的 HTTP client（backend 端）。backend 不自己跑 TTS，改呼叫獨立的 tts 服務。
base_url 走 config（dev=localhost:9002；容器內由 compose 覆寫成 http://tts:9002）。
tts 服務為混合版（線上 edge-tts 為主、離線 MeloTTS 備援），回傳 mp3 或 wav，
故一併回傳 content-type 讓 backend 原樣轉給前端。見 DEVELOPMENT-PLAN.md M3。
"""
import requests

from config import settings


def synthesize(text: str, voice: str | None = None) -> tuple[bytes, str, str]:
    """把文字（+可選語音）送到 TTS 服務，回傳 (音檔 bytes, content_type, engine)。
    engine 為實際使用的引擎：'edge'（線上）或 'melo'（離線 fallback），供前端提示。
    """
    payload: dict = {"text": text}
    if voice:
        payload["voice"] = voice
    try:
        resp = requests.post(
            f"{settings.tts_base_url}/tts",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"TTS 服務呼叫失敗（{settings.tts_base_url}）：{e}")
    return (
        resp.content,
        resp.headers.get("Content-Type", "audio/wav"),
        resp.headers.get("X-TTS-Engine", "edge"),
    )
