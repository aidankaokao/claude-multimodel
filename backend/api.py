"""FastAPI 進入點。直接 `python api.py` 就能跑（底部 uvicorn.run，port 8000）。
見 reference/backend/backend-conventions.md §3。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.engine import engine
from db.tables import metadata
from routers import chat, image, ocr, settings, tts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動：建表（已存在不重建，見 database.md §4）
    metadata.create_all(engine)
    yield
    # 關閉：釋放資源（M1 無）


app = FastAPI(title="multimodel", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發期放寬；正式走 nginx 同源反代其實不需要 CORS（見 deploy）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 路由掛載（所有路徑統一前綴 /api）
app.include_router(chat.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(image.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    # host 0.0.0.0 讓容器對外可達；port 8000 為容器內埠，對外埠由 docker-compose .env 映射。
    uvicorn.run(app, host="0.0.0.0", port=8000)
