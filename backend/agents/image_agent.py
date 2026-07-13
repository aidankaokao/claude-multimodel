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


class ImageState(TypedDict, total=False):
    prompt: str         # 使用者原始描述（可能中文/口語）；generate 模式必填
    mode: str           # "generate"（預設，txt2img）或 "refine"（img2img 微調）
    edit_instruction: str  # refine 模式：使用者的中文修改指令（如「背景改成夜晚」）
    prev_prompt_en: str    # refine 模式：上一輪的英文提示詞（作為合併基底）
    init_image: bytes      # refine 模式：上一張圖 bytes（img2img 起點）
    strength: float        # refine 模式：0~1，越小越保留原圖（預設 0.5）
    prompt_en: str      # LLM 優化/合併後的英文提示詞
    image_bytes: bytes  # generate node 產出


def translate_node(state: ImageState) -> dict:
    """把使用者描述轉成優化英文提示詞。refine 模式則「合併」上一輪提示詞與這次的修改指令。"""
    if state.get("mode") == "refine":
        sys = SystemMessage(
            content=(
                "You are refining an existing image. You get the PREVIOUS English prompt "
                "and a NEW edit instruction (which may be in Chinese). Produce a SINGLE updated "
                "ENGLISH prompt that keeps the previous scene but applies the requested change. "
                "Output ONLY the English prompt — no quotes, no explanation, no line breaks."
            )
        )
        user = HumanMessage(
            content=(
                f"PREVIOUS PROMPT: {state.get('prev_prompt_en', '')}\n"
                f"EDIT INSTRUCTION: {state.get('edit_instruction', '')}"
            )
        )
        fallback = state.get("prev_prompt_en", "") or state.get("edit_instruction", "")
    else:
        sys = SystemMessage(
            content=(
                "You convert a user's image description (which may be in Chinese or casual) "
                "into a SINGLE concise, vivid ENGLISH prompt for a text-to-image model "
                "(Stable Diffusion 1.5). Add helpful visual detail, composition and style keywords. "
                "Output ONLY the English prompt itself — no quotes, no explanation, no line breaks."
            )
        )
        user = HumanMessage(content=state["prompt"])
        fallback = state["prompt"]

    llm = get_chat_model()
    resp = llm.invoke([sys, user])
    prompt_en = (resp.content or "").strip() or fallback
    return {"prompt_en": prompt_en}


def generate_node(state: ImageState) -> dict:
    """依 mode 分流：refine → img2img（帶上一張圖）；否則 → txt2img。"""
    if state.get("mode") == "refine":
        img = image_client.img2img(
            state["prompt_en"],
            state["init_image"],
            state.get("strength", 0.5),
        )
    else:
        img = image_client.generate(state["prompt_en"])
    return {"image_bytes": img}


builder = StateGraph(ImageState)
builder.add_node("translate", translate_node)
builder.add_node("generate", generate_node)
builder.add_edge(START, "translate")
builder.add_edge("translate", "generate")
builder.add_edge("generate", END)

graph = builder.compile()
