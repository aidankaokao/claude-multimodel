"""LLM provider 設定 API（使用者在前端設定頁註冊多筆並選用）。
見 reference/backend/llm-integration.md §5。路由薄，邏輯在 services/llm_provider_service。

- GET    /api/settings/llm-providers        列出（api_key 已遮罩）
- POST   /api/settings/llm-providers        新增一筆
- PUT    /api/settings/llm-providers/{id}   更新（api_key 空字串代表不更動）
- DELETE /api/settings/llm-providers/{id}   刪除
- PUT    /api/settings/llm-active           設定目前選用哪一筆
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import llm_provider_service as svc

router = APIRouter(prefix="/settings")


class ProviderIn(BaseModel):
    name: str
    provider: str  # ollama | openai
    base_url: str
    model: str
    api_key: str | None = None
    temperature: float = 0.0


class ProviderUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None  # 空 / None = 不更動
    temperature: float | None = None


class ActiveIn(BaseModel):
    provider_id: int


def _validate_provider(p: str):
    if p not in ("ollama", "openai"):
        raise HTTPException(status_code=422, detail="provider 只能是 ollama 或 openai")


@router.get("/llm-providers")
def list_llm_providers():
    return svc.list_providers()


@router.post("/llm-providers")
def create_llm_provider(body: ProviderIn):
    _validate_provider(body.provider)
    return svc.create_provider(
        name=body.name, provider=body.provider, base_url=body.base_url,
        model=body.model, api_key=body.api_key, temperature=body.temperature,
    )


@router.put("/llm-providers/{provider_id}")
def update_llm_provider(provider_id: int, body: ProviderUpdate):
    if body.provider is not None:
        _validate_provider(body.provider)
    return svc.update_provider(provider_id, **body.model_dump())


@router.delete("/llm-providers/{provider_id}", status_code=204)
def delete_llm_provider(provider_id: int):
    svc.delete_provider(provider_id)


@router.put("/llm-active")
def set_llm_active(body: ActiveIn):
    svc.set_active_provider(body.provider_id)
    return {"active_provider_id": body.provider_id}
