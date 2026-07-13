"""LLM 建構工廠（有前端版：從 DB 讀使用者註冊、選用的 provider）。
上層一律用 get_chat_model()，不直接 new class、不寫死 base_url / model。
見 reference/backend/llm-integration.md §3、§5.2。
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from services.llm_provider_service import get_active_provider


def get_chat_model(provider_id: int | None = None) -> BaseChatModel:
    """從資料庫取使用者註冊的 provider 設定來建構 chat model。
    provider_id 省略時用專案目前選用（active）那筆。
    上層用法（invoke / stream / bind_tools）與 .env 版完全相同。

    provider="ollama" -> 本地 Ollama server 託管模型
    provider="openai" -> 外部 OpenAI 或本地 vLLM（OpenAI 相容 API）
    """
    cfg = get_active_provider(provider_id)  # {provider, base_url, model, api_key, temperature, ...}

    if cfg["provider"] == "ollama":
        return ChatOllama(
            model=cfg["model"],
            base_url=cfg["base_url"],
            temperature=cfg.get("temperature", 0.0),
        )
    if cfg["provider"] == "openai":  # 外部 OpenAI 或本地 vLLM
        return ChatOpenAI(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=cfg.get("api_key") or "EMPTY",  # vLLM 常不驗 key
            temperature=cfg.get("temperature", 0.0),
        )
    raise ValueError(f"未知的 provider: {cfg['provider']!r}")
