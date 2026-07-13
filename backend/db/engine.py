"""SQLAlchemy Core Engine。唯一的 DB 差異處理集中在這裡（SQLite check_same_thread）。
見 reference/backend/database.md §3。
"""
from sqlalchemy import create_engine

from config import settings

# SQLite 需要 check_same_thread=False 才能在多執行緒（FastAPI）用同一連線
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,  # 連線失效自動重連（PostgreSQL 尤其需要）
    future=True,
)
