"""文生圖推論服務（獨立容器）。用 diffusers + Stable Diffusion 1.5（開源，OpenRAIL 可商用）。
自動偵測裝置：有可用 CUDA GPU 就用 GPU（快），否則自動用 CPU（慢但可跑）。
與 backend 分離：backend 只透過 HTTP 呼叫本服務。維持 POST /generate 介面。
沿用專案慣例：進入點 api.py + 底部 uvicorn.run；容器內固定埠 9003、CMD python api.py。
"""
import io
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

# SD 1.5（Runway 原 repo 已下架，改用社群 re-host 版；可用 SD_MODEL 覆寫）
MODEL_ID = os.getenv("SD_MODEL", "stable-diffusion-v1-5/stable-diffusion-v1-5")
DEFAULT_SIZE = int(os.getenv("SD_SIZE", "512"))

_PIPE = None
_DEVICE = "cpu"


def _get_pipe():
    global _PIPE, _DEVICE
    if _PIPE is None:
        import torch
        from diffusers import StableDiffusionPipeline

        try:
            cuda = torch.cuda.is_available()
        except Exception:  # noqa: BLE001 (驅動異常等，一律當作沒有 GPU)
            cuda = False
        _DEVICE = "cuda" if cuda else "cpu"
        dtype = torch.float16 if _DEVICE == "cuda" else torch.float32

        pipe = StableDiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
            safety_checker=None,          # 教學用：關掉 NSFW filter，避免誤判整張變黑
            requires_safety_checker=False,
        )
        pipe = pipe.to(_DEVICE)
        pipe.enable_attention_slicing()   # 降低記憶體用量
        _PIPE = pipe
        print(f"[image] Stable Diffusion 載入完成，device={_DEVICE}")
    return _PIPE


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_pipe()  # 啟動時下載/載入模型（SD 1.5 約 4GB）
    yield


app = FastAPI(title="image-service", version="0.1.0", lifespan=lifespan)


class GenIn(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    steps: int | None = None
    width: int | None = None
    height: int | None = None
    seed: int | None = None


@app.get("/health")
def health():
    return {"status": "ok", "device": _DEVICE}


@app.post("/generate")
def generate(body: GenIn):
    """收 {prompt,...} → 回 PNG 圖片（image/png）。同步端點由 FastAPI 丟 threadpool，不擋事件迴圈。"""
    import torch

    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt 不可為空")

    pipe = _get_pipe()
    steps = body.steps or (30 if _DEVICE == "cuda" else 20)  # CPU 少步數省時間
    width = body.width or DEFAULT_SIZE
    height = body.height or DEFAULT_SIZE

    generator = None
    if body.seed is not None:
        generator = torch.Generator(device=_DEVICE).manual_seed(body.seed)

    image = pipe(
        prompt,
        negative_prompt=body.negative_prompt,
        num_inference_steps=steps,
        width=width,
        height=height,
        generator=generator,
    ).images[0]

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png", headers={"X-Device": _DEVICE})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9003)
