"""文字問答 API。掛在 /api（見 backend-conventions.md §3；agent 見 langgraph-agent.md §7）。
路由薄、邏輯在 agent/service。提供同步 /chat 與串流 /chat/stream（逐字輸出）。
串流見 langgraph-agent.md §6（graph.stream）＋ frontend-backend-integration.md §5（前端讀 stream）。
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, AIMessageChunk,
)
from pydantic import BaseModel

from agents.chat_agent import graph
from llm import get_chat_model

router = APIRouter()


class Turn(BaseModel):
    role: str  # user | assistant | system
    content: str


class ChatIn(BaseModel):
    message: str
    history: list[Turn] = []


class ChatOut(BaseModel):
    reply: str


def _to_lc_messages(history: list[Turn], message: str):
    msgs = []
    for t in history:
        if t.role == "user":
            msgs.append(HumanMessage(content=t.content))
        elif t.role == "assistant":
            msgs.append(AIMessage(content=t.content))
        elif t.role == "system":
            msgs.append(SystemMessage(content=t.content))
    msgs.append(HumanMessage(content=message))
    return msgs


@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    try:
        result = graph.invoke({"messages": _to_lc_messages(body.history, body.message)})
    except ValueError as e:
        # 常見：尚未設定 provider（見 llm_provider_service.get_active_provider）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM 呼叫失敗：{e}")
    return {"reply": result["messages"][-1].content}


@router.post("/chat/stream")
def chat_stream(body: ChatIn):
    """逐字串流回覆（純文字 chunk）。前端讀 ReadableStream 逐段附加顯示。
    nginx 已關 buffering（見 frontend-backend-integration.md §3），逐字才不會被卡住。
    """
    # 開始串流前先驗證 provider 已設定，好回乾淨的 400（串流一旦開始只能回 200）
    try:
        get_chat_model()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    msgs = _to_lc_messages(body.history, body.message)

    def gen():
        try:
            # stream_mode="messages"：streams LLM token（node 內 LLM 逐字產生）
            for chunk, _meta in graph.stream({"messages": msgs}, stream_mode="messages"):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    yield chunk.content
        except Exception as e:
            # 串流中途出錯：以文字回報（此時 HTTP 已是 200），前端會顯示這段
            yield f"\n\n[錯誤] LLM 呼叫失敗：{e}"

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")
