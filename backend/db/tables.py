"""Core Table 定義（MetaData）。用可攜通用型別，換 DB 只改 DATABASE_URL。
見 reference/backend/database.md §4。

M1 表：
- llm_providers：使用者在設定頁註冊的多個 LLM provider（llm-integration.md §5）。
- app_settings ：簡單 key/value，存「目前選用哪一筆 provider」等全域設定。
"""
from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, Text, Float, DateTime, func,
)

metadata = MetaData()

# 使用者註冊的 LLM provider（可多筆）。api_key 存後端、不回傳明文給前端（服務層遮罩）。
llm_providers = Table(
    "llm_providers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(120), nullable=False),          # 顯示名稱（好認）
    Column("provider", String(20), nullable=False),       # ollama | openai
    Column("base_url", String(300), nullable=False),
    Column("model", String(200), nullable=False),
    Column("api_key", Text, nullable=True),               # openai 類需要；vLLM 可 EMPTY
    Column("temperature", Float, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

# 全域 key/value 設定（如 active_provider_id）
app_settings = Table(
    "app_settings",
    metadata,
    Column("key", String(80), primary_key=True),
    Column("value", Text, nullable=True),
)
