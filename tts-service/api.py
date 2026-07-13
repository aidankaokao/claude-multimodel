"""TTS 推論服務（獨立容器）· 混合版。
  1) 先試 edge-tts（線上，微軟 Edge 免費語音）—— 自然、有台灣腔、有男女聲、快、可指定 voice。
  2) 失敗（無網路 / 逾時 / 錯誤）→ 自動 fallback 到 MeloTTS（離線開源，中文女聲）。

維持 POST /tts 介面：收 {text, voice?} → 回音檔（edge 回 mp3、melo 回 wav；前端用 blob 播放皆可）。
換引擎不影響 backend / 前端。容器內固定埠 9002、CMD python api.py。
"""
import asyncio
import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

# 預設 edge-tts 語音（前端可用 voice 覆寫）。台灣女聲。
DEFAULT_VOICE = os.getenv("TTS_VOICE", "zh-TW-HsiaoChenNeural")
EDGE_TIMEOUT = float(os.getenv("EDGE_TTS_TIMEOUT", "20"))  # 線上逾時就 fallback

# 離線 MeloTTS 設定
LANGUAGE = os.getenv("TTS_LANGUAGE", "ZH")
SPEED = float(os.getenv("TTS_SPEED", "1.0"))

_MODEL = None
_SPEAKER_ID = None


# ── 離線：MeloTTS ────────────────────────────────────────────────
def _get_model():
    global _MODEL, _SPEAKER_ID
    if _MODEL is None:
        from melo.api import TTS

        _MODEL = TTS(language=LANGUAGE, device="cpu")
        _SPEAKER_ID = _MODEL.hps.data.spk2id[LANGUAGE]
    return _MODEL, _SPEAKER_ID


def _melo_synth(text: str) -> bytes:
    model, sid = _get_model()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    try:
        model.tts_to_file(text, sid, tmp.name, speed=SPEED)
        with open(tmp.name, "rb") as fh:
            return fh.read()
    finally:
        os.remove(tmp.name)


# ── 線上：edge-tts ───────────────────────────────────────────────
async def _edge_synth(text: str, voice: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    buf = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.extend(chunk["data"])
    if not buf:
        raise RuntimeError("edge-tts 無音訊輸出")
    return bytes(buf)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 預熱離線 MeloTTS（趁有網路先下載/載入好，之後離線 fallback 才有得用）。
    # 失敗不擋啟動：仍可靠線上 edge-tts 服務。
    try:
        await asyncio.to_thread(_get_model)
    except Exception as e:  # noqa: BLE001
        print(f"[tts] MeloTTS 預熱失敗（fallback 將不可用）：{e}")
    yield


app = FastAPI(title="tts-service", version="0.3.0", lifespan=lifespan)


class TtsIn(BaseModel):
    text: str
    voice: str | None = None  # edge-tts 語音名（如 zh-TW-YunJheNeural）；省略用預設


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tts")
async def tts(body: TtsIn):
    """先線上 edge-tts、失敗自動離線 MeloTTS。回音檔（mp3 或 wav）。"""
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 不可為空")
    voice = body.voice or DEFAULT_VOICE

    # 1) 線上 edge-tts
    try:
        audio = await asyncio.wait_for(_edge_synth(text, voice), timeout=EDGE_TIMEOUT)
        return Response(content=audio, media_type="audio/mpeg", headers={"X-TTS-Engine": "edge"})
    except Exception as edge_err:  # noqa: BLE001
        print(f"[tts] edge-tts 失敗，改用離線 MeloTTS：{edge_err}")

    # 2) 離線 MeloTTS fallback
    try:
        audio = await asyncio.to_thread(_melo_synth, text)
        return Response(content=audio, media_type="audio/wav", headers={"X-TTS-Engine": "melo"})
    except Exception as melo_err:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"TTS 失敗（線上與離線皆不可用）：{melo_err}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9002)
