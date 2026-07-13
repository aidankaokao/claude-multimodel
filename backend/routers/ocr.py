"""圖片 OCR API。掛在 /api。multipart 上傳圖片 → ocr_agent（辨識 + LLM 整理）。
路由薄，流程在 agents/ocr_agent（OCR 呼叫在 services/ocr_client）。
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from agents.ocr_agent import graph

router = APIRouter()


@router.post("/ocr")
async def ocr(file: UploadFile = File(...), instruction: str = Form("")):
    """回 { ocr_text: 原始辨識文字, organized: LLM 整理後 }。"""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="沒有收到圖片內容")
    try:
        result = graph.invoke({"image_bytes": data, "instruction": instruction})
    except ValueError as e:
        # 常見：尚未設定 LLM provider（整理步驟需要）
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # OCR 服務呼叫失敗（見 ocr_client）
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR 流程失敗：{e}")
    return {"ocr_text": result.get("ocr_text", ""), "organized": result.get("answer", "")}
