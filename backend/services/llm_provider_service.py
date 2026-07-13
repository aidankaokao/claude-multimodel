"""LLM provider 設定的商業邏輯（存 DB，使用者在前端設定頁註冊多筆並選用）。
見 reference/backend/llm-integration.md §5、database.md §5。

- 對前端（router）暴露的資料一律「遮罩 api_key」，不回傳明文。
- 對內（llm 工廠）用 get_active_provider() 取真正的 key 來建構 model。
- 所有 DB 操作走 SQLAlchemy Core 表達式，不拼字串 SQL。
"""
from sqlalchemy import select, insert, update, delete

from db.engine import engine
from db.tables import llm_providers, app_settings

_ACTIVE_KEY = "active_provider_id"


# ── app_settings 小工具 ─────────────────────────────────────────────
def _get_setting(key: str) -> str | None:
    with engine.connect() as conn:
        row = conn.execute(
            select(app_settings.c.value).where(app_settings.c.key == key)
        ).first()
        return row[0] if row else None


def _set_setting(key: str, value: str | None) -> None:
    with engine.begin() as conn:
        exists = conn.execute(
            select(app_settings.c.key).where(app_settings.c.key == key)
        ).first()
        if exists:
            conn.execute(
                update(app_settings).where(app_settings.c.key == key).values(value=value)
            )
        else:
            conn.execute(insert(app_settings).values(key=key, value=value))


# ── 遮罩 ────────────────────────────────────────────────────────────
def _mask_key(api_key: str | None) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 4:
        return "****"
    return f"{api_key[:2]}****{api_key[-2:]}"


def _to_public(row: dict) -> dict:
    """回傳給前端用：遮罩 api_key、附上是否為 active。"""
    active_id = get_active_provider_id()
    return {
        "id": row["id"],
        "name": row["name"],
        "provider": row["provider"],
        "base_url": row["base_url"],
        "model": row["model"],
        "api_key_masked": _mask_key(row.get("api_key")),
        "has_api_key": bool(row.get("api_key")),
        "temperature": row["temperature"],
        "is_active": row["id"] == active_id,
    }


# ── CRUD（給 router / 設定頁）─────────────────────────────────────────
def list_providers() -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(select(llm_providers).order_by(llm_providers.c.created_at.desc()))
        return [_to_public(dict(r._mapping)) for r in rows]


def create_provider(
    name: str, provider: str, base_url: str, model: str,
    api_key: str | None = None, temperature: float = 0.0,
) -> dict:
    with engine.begin() as conn:
        result = conn.execute(
            insert(llm_providers).values(
                name=name, provider=provider, base_url=base_url,
                model=model, api_key=api_key or None, temperature=temperature,
            )
        )
        new_id = result.inserted_primary_key[0]
    # 若尚未有 active，第一筆自動設為 active
    if get_active_provider_id() is None:
        set_active_provider(new_id)
    return _get_public_by_id(new_id)


def update_provider(provider_id: int, **fields) -> dict:
    """只更新有帶進來的欄位。api_key 帶空字串代表「不更動」（前端只在改 key 時才送新值）。"""
    values = {}
    for col in ("name", "provider", "base_url", "model", "temperature"):
        if col in fields and fields[col] is not None:
            values[col] = fields[col]
    # api_key：None 或空 → 不動；有值 → 覆寫
    api_key = fields.get("api_key")
    if api_key:
        values["api_key"] = api_key

    if values:
        with engine.begin() as conn:
            conn.execute(
                update(llm_providers).where(llm_providers.c.id == provider_id).values(**values)
            )
    return _get_public_by_id(provider_id)


def delete_provider(provider_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(llm_providers).where(llm_providers.c.id == provider_id))
    # 刪掉的若是 active，清掉 active 設定
    if get_active_provider_id() == provider_id:
        _set_setting(_ACTIVE_KEY, None)


# ── active 選用 ─────────────────────────────────────────────────────
def get_active_provider_id() -> int | None:
    raw = _get_setting(_ACTIVE_KEY)
    return int(raw) if raw else None


def set_active_provider(provider_id: int) -> None:
    _set_setting(_ACTIVE_KEY, str(provider_id))


# ── 內部用：取真正的設定（含明文 key）給 llm 工廠 ─────────────────────
def get_active_provider(provider_id: int | None = None) -> dict:
    """回傳一筆可用配置（含真實 api_key），給 llm/__init__.py 建構 model 用。
    provider_id 省略 → 用目前選用（active）那筆。
    """
    pid = provider_id or get_active_provider_id()
    if pid is None:
        raise ValueError("尚未設定任何 LLM provider，請先在設定頁註冊並選用。")
    with engine.connect() as conn:
        row = conn.execute(
            select(llm_providers).where(llm_providers.c.id == pid)
        ).first()
    if row is None:
        raise ValueError(f"找不到 provider id={pid}")
    return dict(row._mapping)


def _get_public_by_id(provider_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            select(llm_providers).where(llm_providers.c.id == provider_id)
        ).first()
    return _to_public(dict(row._mapping))
