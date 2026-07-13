"""文字轉圖片 API。掛在 /api。文字（中文可）→ image_agent（LLM 翻譯優化 → 生圖）→ 回圖。
路由薄，流程在 agents/image_agent（生圖呼叫在 services/image_client）。
回 JSON：同時帶「優化後英文提示詞」與「圖片(base64 data URL)」，方便前端顯示兩者。
"""
import base64

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.image_agent import graph

router = APIRouter()


class ImageIn(BaseModel):
    prompt: str


@router.post("/image")
def image(body: ImageIn):
    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt 不可為空")
    try:
        result = graph.invoke({"prompt": prompt})
    except ValueError as e:
        # 常見：尚未設定 LLM provider（翻譯步驟需要）
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # 文生圖服務呼叫失敗（見 image_client）
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"文生圖流程失敗：{e}")

    b64 = base64.b64encode(result["image_bytes"]).decode()
    return {
        "prompt_en": result.get("prompt_en", ""),
        "image": f"data:image/png;base64,{b64}",
    }
