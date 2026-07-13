"""文字問答 agent（LangGraph StateGraph）。M1 先做最小對話：
messages 進 -> LLM node -> messages 出。之後里程碑再加「判斷多模態需求」的條件分支
（route -> ocr / tts / image ... tool node），見 langgraph-agent.md §4。
LLM 建構外包給 llm/（不在 node 裡硬編 model / base_url），見 langgraph-agent.md §5。
"""
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from llm import get_chat_model


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # 對話訊息累加


def llm_node(state: State) -> dict:
    llm = get_chat_model()  # ChatOllama 或 ChatOpenAI，依 DB active provider
    resp = llm.invoke(state["messages"])
    return {"messages": [resp]}


builder = StateGraph(State)
builder.add_node("llm", llm_node)
builder.add_edge(START, "llm")
builder.add_edge("llm", END)

graph = builder.compile()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    result = graph.invoke({"messages": [HumanMessage(content="用一句話介紹台灣。")]})
    print(result["messages"][-1].content)
