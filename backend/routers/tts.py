"""文字轉語音 API。掛在 /api。純工具型：文字 → 呼叫獨立 TTS 服務 → 回 WAV 音檔。
不經 LLM / agent（TTS 非 LLM 流程）；邏輯在 services/tts_client。
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from services import tts_client

router = APIRouter()


class TtsIn(BaseModel):
    text: str
    voice: str | None = None  # edge-tts 語音（如 zh-TW-YunJheNeural）；省略用服務預設


@router.post("/tts")
def tts(body: TtsIn):
    """回音檔（mp3 或 wav，依 TTS 服務實際用的引擎）。前端拿到 blob 直接播放。"""
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 不可為空")
    try:
        audio, content_type, engine = tts_client.synthesize(text, body.voice)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS 失敗：{e}")
    # X-TTS-Engine：edge(線上) / melo(離線 fallback)，前端據此提示是否為離線語音
    return Response(content=audio, media_type=content_type, headers={"X-TTS-Engine": engine})
