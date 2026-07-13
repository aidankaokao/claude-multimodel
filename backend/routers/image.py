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


class RefineIn(BaseModel):
    edit_instruction: str      # 使用者中文修改指令（如「背景改成夜晚」）
    init_image: str            # 上一張圖（base64 data URL）
    prev_prompt_en: str = ""   # 上一輪英文提示詞（作為合併基底）
    strength: float | None = None  # 0~1，越小越保留原圖


def _result_to_json(result: dict) -> dict:
    b64 = base64.b64encode(result["image_bytes"]).decode()
    return {
        "prompt_en": result.get("prompt_en", ""),
        "image": f"data:image/png;base64,{b64}",
    }


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

    return _result_to_json(result)


@router.post("/image/refine")
def refine(body: RefineIn):
    """對話式微調：以上一張圖為起點（img2img），套用中文修改指令重繪。"""
    instruction = (body.edit_instruction or "").strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="修改指令不可為空")

    # 解 init image（data URL → bytes）
    raw = (body.init_image or "").strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        init_bytes = base64.b64decode(raw, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="init_image 解析失敗")
    if not init_bytes:
        raise HTTPException(status_code=400, detail="init_image 不可為空")

    state = {
        "mode": "refine",
        "edit_instruction": instruction,
        "prev_prompt_en": body.prev_prompt_en or "",
        "init_image": init_bytes,
    }
    if body.strength is not None:
        state["strength"] = body.strength

    try:
        result = graph.invoke(state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"圖片微調流程失敗：{e}")

    return _result_to_json(result)
