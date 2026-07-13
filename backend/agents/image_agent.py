"""文生圖 agent（LangGraph）。兩段式流水線：
  translate node（LLM 把中文/口語描述轉成優化過的英文提示詞）→ generate node（呼叫文生圖服務）→ END

SD 系列對英文提示詞效果好很多，故先用 LLM 翻譯優化（延續 OCR 那種「agent 中用 LLM」的做法）。
副作用（呼叫文生圖服務）走 services/；LLM 建構外包給 llm/。見 langgraph-agent.md §2、§5。
"""
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from llm import get_chat_model
from services import image_client


class ImageState(TypedDict):
    prompt: str        # 使用者原始描述（可能中文/口語）
    prompt_en: str     # LLM 優化後的英文提示詞
    image_bytes: bytes # generate node 產出


def translate_node(state: ImageState) -> dict:
    sys = SystemMessage(
        content=(
            "You convert a user's image description (which may be in Chinese or casual) "
            "into a SINGLE concise, vivid ENGLISH prompt for a text-to-image model "
            "(Stable Diffusion 1.5). Add helpful visual detail, composition and style keywords. "
            "Output ONLY the English prompt itself — no quotes, no explanation, no line breaks."
        )
    )
    user = HumanMessage(content=state["prompt"])
    llm = get_chat_model()
    resp = llm.invoke([sys, user])
    prompt_en = (resp.content or "").strip() or state["prompt"]
    return {"prompt_en": prompt_en}


def generate_node(state: ImageState) -> dict:
    img = image_client.generate(state["prompt_en"])
    return {"image_bytes": img}


builder = StateGraph(ImageState)
builder.add_node("translate", translate_node)
builder.add_node("generate", generate_node)
builder.add_edge(START, "translate")
builder.add_edge("translate", "generate")
builder.add_edge("generate", END)

graph = builder.compile()
