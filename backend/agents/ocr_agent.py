"""圖片 OCR agent（LangGraph）。兩段式流水線：
  ocr node（呼叫獨立 OCR 服務辨識）→ organize node（LLM 整理辨識結果）→ END

副作用（呼叫 OCR 服務）走 services/，node 保持薄；LLM 建構外包給 llm/。
見 reference/backend/langgraph-agent.md §2、§5。
"""
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from llm import get_chat_model
from services import ocr_client


class OcrState(TypedDict):
    image_bytes: bytes   # 輸入圖片
    instruction: str     # 使用者附帶指示（可空）
    ocr_text: str        # ocr node 產出
    answer: str          # organize node 產出（整理後）


def ocr_node(state: OcrState) -> dict:
    text = ocr_client.recognize(state["image_bytes"])
    return {"ocr_text": text}


def organize_node(state: OcrState) -> dict:
    ocr_text = state.get("ocr_text", "").strip()
    if not ocr_text:
        return {"answer": "（圖片中未辨識到文字）"}

    instruction = (state.get("instruction") or "").strip()
    sys = SystemMessage(
        content=(
            "你是文件整理助理。以下是對一張圖片做 OCR 得到的原始文字，"
            "可能有斷行、雜訊或辨識錯誤。請用繁體中文，將它整理成通順、結構清楚的內容"
            "（適當分段、修正明顯的辨識錯字、保留原意）。若使用者有額外指示，優先照做。"
        )
    )
    user = HumanMessage(
        content=(
            (f"使用者指示：{instruction}\n\n" if instruction else "")
            + f"OCR 原始文字：\n{ocr_text}"
        )
    )
    llm = get_chat_model()  # 依 DB active provider
    resp = llm.invoke([sys, user])
    return {"answer": resp.content}


builder = StateGraph(OcrState)
builder.add_node("ocr", ocr_node)
builder.add_node("organize", organize_node)
builder.add_edge(START, "ocr")
builder.add_edge("ocr", "organize")
builder.add_edge("organize", END)

graph = builder.compile()
