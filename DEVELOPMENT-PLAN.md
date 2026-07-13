# multimodel 開發計劃書

> 專案細節放這份；根目錄 `CLAUDE.md` 保持精簡並指向這裡。
> 慣例一律以 `reference/` 為準，需求以 `reference/PROJECT-REQUIREMENTS.md` 為準。

## 專案目標

多模態問答界面：用開源方式與模型建構各種多模態交互（文字轉語音、文字轉圖片、圖片 OCR…），
**以教學方式、從簡單到困難**逐步建立。

## 關鍵決策（已與開發者確認）

1. **前端風格**：Aurora Glass（極光琉璃），可切主題盤（`reference/frontend/frontend-style-aurora-glass.md`）。
2. **LLM provider 設定來源**：有前端 → 使用者在**設定頁註冊多筆、存 DB、選用**（`llm-integration.md §5`）。
3. **AI agent**：LangGraph `StateGraph`（`langgraph-agent.md`）。
4. **資料庫**：SQLAlchemy Core，初期 SQLite（`database.md`）。
5. **多模態模型執行方式**：**各自獨立推論服務（多容器）** — backend 只透過 HTTP 呼叫，
   每種模型（OCR / TTS / 文生圖）獨立起一個服務/容器。**只能用開源 / 免費套件與模型。**
6. **部署**：Docker Compose，`APP_ROUTE=multimodel`、`IMAGE_PREFIX=multimodel`（`deploy-guide.md`）。

## 進度總覽（To-Do）

> 勾選狀態即進度。`[x]` 完成、`[ ]` 未做、`[~]` 進行中。細項在各里程碑段落。

| 里程碑 | 狀態 | 摘要 |
|---|---|---|
| **M1** 文字問答打底 + Provider 設定頁 | ✅ 完成 | 全鏈路跑通、串流、Markdown、UI 調整 |
| **M2** 圖片 OCR（第一個多模態）| ✅ 完成 | 獨立 OCR 服務(PaddleOCR) + ocr_agent + 前端上傳 |
| **M3** 文字轉語音（TTS）| ✅ 完成 | 混合 edge-tts(線上)+MeloTTS(離線) + 語音可切 + 🔊 |
| **M4** 文字轉圖片 | ✅ 完成 | 獨立文生圖服務(SD1.5，自動GPU/CPU) + LLM 翻譯提示詞 |
| 增強 / 技術債 | ◻ 待辦 | 見「增強 backlog」段 |

### M1 已完成項目
- [x] 後端骨架（api.py / config / db / services / llm / agents / routers）
- [x] LLM Provider 設定頁（DB 註冊多筆 + 選用 + 金鑰遮罩）
- [x] LangGraph 文字問答 agent
- [x] 問答串流逐字輸出（`/api/chat/stream`）
- [x] Markdown 渲染助理回覆
- [x] Aurora Glass 前端（Sidebar 折疊/拖曳、Header 主題切換、8 套主題盤）
- [x] Docker 容器部署跑通（`/multimodel/` 路由）
- [x] UI 調整：聊天無外層卡片、加寬至 max-w-5xl、修掉初始溢出捲軸

### M2 已完成項目
- [x] 開源 OCR 推論服務（**PaddleOCR，繁中 `chinese_cht`**）獨立容器 `ocr-service/`（FastAPI，埠 9001）
- [x] 後端 `services/ocr_client.py`（HTTP 呼叫 OCR 服務）
- [x] 後端 `routers/ocr.py`：`POST /api/ocr`（multipart 圖片上傳）
- [x] LangGraph `agents/ocr_agent.py`：OCR node → LLM 整理 node（辨識後**自動交給 LLM 整理**）
- [x] 前端：聊天頁圖片上傳 UI + 縮圖 + 整理結果（Markdown）+ 可展開原始 OCR 文字
- [x] compose 新增 `ocr` service + backend 以 `http://ocr:9001` 呼叫 + `build.sh` 加 OCR image

### M3 已完成項目
- [x] 開源 TTS 服務（**MeloTTS，MIT**）獨立容器 `tts-service/`（FastAPI，埠 9002，ZH 中英混讀）
- [x] 後端 `services/tts_client.py` + `routers/tts.py`（`POST /api/tts` → 回 `audio/wav`）
- [x] 前端：助理回覆 🔊 播放鈕（同文字快取，不重複合成）
- [x] compose 新增 `tts` service + `build.sh` 加 TTS image
- [x] 引擎演進：Piper → MeloTTS →**混合（edge-tts 線上為主 + MeloTTS 離線備援）**
- [x] 前端語音下拉：台女/台男/陸女/陸男（edge-tts）；離線 fallback 為 MeloTTS 女聲
- [x] 離線提示：fallback 到離線時跳 toast + 語音選單旁顯示「離線語音」標籤（引擎資訊經 `X-TTS-Engine` 標頭傳到前端；離線結果不快取，恢復連線自動重試線上）

### M4 已完成項目
- [x] 開源文生圖服務（**Stable Diffusion 1.5，OpenRAIL 可商用**）獨立容器 `image-service/`（FastAPI，埠 9003）
- [x] **自動偵測裝置**：有 CUDA GPU 就用，否則自動 CPU（`torch.cuda.is_available()`，異常也退回 CPU）
- [x] 後端 `services/image_client.py` + `agents/image_agent.py`（**LLM 翻譯優化中文→英文提示詞** → 生圖）+ `routers/image.py`（`POST /api/image`）
- [x] 前端：輸入列「生成圖片」鈕 → 顯示圖片 + 下載 + 可展開英文提示詞
- [x] compose 新增 `image` service（GPU passthrough 註解備用）+ `build.sh` 加 image image

### 增強 backlog（隨時可做，非里程碑）
- [ ] 文生圖：可調 steps/尺寸/negative prompt/seed（目前用預設）
- [ ] 長文字朗讀延遲：句子級串流（切句、逐句先播）—— 主要對離線 MeloTTS fallback 有感
- [ ] 統一入口：讓 `chat_agent` 自行判斷多模態需求並分流（目前各模態走各自 `/api/*`）
- [ ] OCR 結果串流整理（目前 `/api/ocr` 為同步回傳）
- [ ] 程式碼語法高亮（`rehype-highlight`，開源）
- [ ] 對話「新開/清空」與多會話管理
- [ ] 串流中「停止產生」按鈕（AbortController）
- [ ] Provider 連線測試按鈕（設定頁按一下驗證能否連上）

---

## 架構總覽

```
前端 (Aurora Glass, Vite/React)  ──同源 /api──▶  前端 nginx ──▶  backend (FastAPI)
                                                                   │
                                                    LangGraph agent（判斷多模態需求）
                                                                   │
                            ┌──────────────┬──────────────┬────────┴─────────┐
                        Chat LLM        OCR 服務        TTS 服務          文生圖服務
                     (Ollama/OpenAI/    (獨立容器)     (獨立容器)         (獨立容器)
                        vLLM)            ── M2+ 依里程碑逐一加入，backend 以 HTTP 呼叫 ──
```

- backend 對每個推論服務寫一個 `services/<modality>_client.py`（HTTP client），LangGraph 以 tool node 呼叫。
- 每個推論服務有自己的 `Dockerfile` 與 compose service，走同一 `custom-network`，backend 用 service 名稱內網呼叫。
- provider 設定頁未來可擴充成「各模態各自選用哪個服務 / 模型」。

## 里程碑

### ✅ M1 — 文字問答打底 + Provider 設定頁（本次完成）

全鏈路先跑通，作為所有多模態的共同基礎。

**後端 `backend/`**（結構見 `backend-conventions.md §4`）
- `api.py`：FastAPI + lifespan 建表 + CORS + `/api/health` + 掛 router；`python api.py` 起 port 8000。
- `config.py`：pydantic-settings（`database_url` / `app_env`）。
- `db/engine.py`、`db/tables.py`：Core；表 `llm_providers`（多筆註冊）、`app_settings`（存 active id）。
- `services/llm_provider_service.py`：provider CRUD + active 選用 + 金鑰遮罩；`get_active_provider()` 給工廠。
- `llm/__init__.py`：`get_chat_model()` 從 DB active 讀，建 `ChatOllama` / `ChatOpenAI`（`llm-integration.md §5.2`）。
- `agents/chat_agent.py`：LangGraph `StateGraph`，`messages`(add_messages) → `llm` node → END。
- `routers/chat.py`：`POST /api/chat`（同步）＋ `POST /api/chat/stream`（**串流逐字**，`graph.stream(stream_mode="messages")` → `StreamingResponse` 純文字 chunk）。
- `routers/settings.py`：`/api/settings/llm-providers` CRUD、`PUT /api/settings/llm-active`。

**前端 `frontend/`**（Aurora Glass）
- 起手檔：`package.json`(+sonner、react-markdown、remark-gfm)、`vite.config.ts`、`tsconfig*`、`postcss.config.js`、`index.html`、`nginx.conf(.template)`、`.env.example`。
- 聊天串流：`lib/api.ts` 的 `postStream()` 讀 ReadableStream 逐字附加；`components/Markdown.tsx`（react-markdown + gfm）渲染助理回覆，樣式在 `index.css` 的 `.markdown-body`。
- `tailwind.config.js`、`src/index.css`（tokens + `.glass` + 8 套主題盤）。
- `src/lib/utils.ts`(cn)、`src/lib/api.ts`(薄 client)、`src/lib/themes.ts`、`src/stores/pageHeader.ts`。
- `src/components/`：`GlassBackground`、`ui/`(button/card/input/textarea/label/badge/select)、`layout/`(Sidebar 可折疊+拖曳、Header 含主題切換、AppLayout)。
- `src/pages/`：`ChatPage`（聊天）、`SettingsProvidersPage`（provider CRUD + 選用）。
- `src/App.tsx`（Router，basename=BASE_URL）、`src/main.tsx`。

**部署**：根目錄 `.env(.example)`（`APP_ROUTE=multimodel`）；`docker-compose.yaml`/`Dockerfile.*`/`build.sh` 沿用起手檔。

**M1 驗收**：註冊一個 provider → 選用 → 在聊天頁問答得到回覆。

### ✅ M2 — 第一個多模態：圖片 OCR（完成）

**決策**：PaddleOCR、繁中為主（`chinese_cht`）、辨識後**自動交給 LLM 整理**。
維持「多容器」架構：OCR 是**獨立推論服務**，backend 只用 HTTP 呼叫，全開源。

**流程**：聊天頁上傳圖片（可附指示）→ `POST /api/ocr`（multipart）→ `ocr_agent`：
`ocr node`（呼叫 `ocr-service`）→ `organize node`（`get_chat_model()` 整理成通順繁中）→ 回 `{ocr_text, organized}`。

**已建檔案**
- [x] `ocr-service/`：`api.py`（FastAPI + PaddleOCR，`POST /ocr`，埠 9001）、`requirements.txt`。
- [x] `Dockerfile.ocr`（root；裝 `libgl1`/`libglib2.0-0`）。
- [x] `backend/services/ocr_client.py`（HTTP client，讀 `settings.ocr_base_url`）。
- [x] `backend/agents/ocr_agent.py`（OCR → LLM 整理，兩節點流水線）。
- [x] `backend/routers/ocr.py`（`POST /api/ocr`），掛進 `api.py`。
- [x] `backend/config.py` 加 `ocr_base_url`；`requirements.txt` 加 `python-multipart`、`requests`。
- [x] 前端 `ChatPage`：上傳鈕 + 預覽 + OCR 結果（Markdown）+ 展開原始文字；`api.ts` 加 `postForm`。
- [x] `docker-compose.yaml` 加 `ocr` service（backend `OCR_BASE_URL=http://ocr:9001` + `depends_on`）；`build.sh` 加 OCR image。

**M2 驗收**：聊天頁上傳一張含文字的圖片 → 得到整理後的繁中文字（可展開看原始 OCR）。

> ⚠️ OCR image 較大：`paddleocr`/`paddlepaddle` 首次 build 會下載大量套件、首次啟動下載模型（已掛 `./ocr-service/models` volume 快取），耗時較久屬正常。

### ✅ M3 — 文字轉語音（TTS，完成）

**決策演進**：Piper（英文念成中文、機械）→ MeloTTS（修好混讀但大陸腔、CPU 慢、只女聲）→ **混合版**。
**最終＝混合**：`tts-service` **先試線上 edge-tts**（自然、台灣腔、有男女聲、快），**失敗自動 fallback 離線 MeloTTS**（保底）。
一次解決：男女聲/台灣腔、速度、線上離線自動切換。轉語音對象＝**LLM 回覆加 🔊 播放鈕**。

**語音**（前端可切，存 localStorage）：`zh-TW-HsiaoChenNeural`(台女)、`zh-TW-YunJheNeural`(台男)、`zh-CN-XiaoxiaoNeural`(陸女)、`zh-CN-YunxiNeural`(陸男)。離線 fallback 時固定 MeloTTS 中文女聲。

**流程**：前端 🔊 →（帶所選 voice）`POST /api/tts {text, voice}` → backend 轉呼 `tts-service`（edge→melo）→ 回音檔（mp3 或 wav，content-type 原樣轉）→ 前端播放（**voice+text 快取**，不重播不重合成）。TTS 工具型、不經 LLM/agent。

**已建檔案**
- [x] `tts-service/api.py`（**混合**：edge-tts 主 + MeloTTS fallback；`POST /tts` 收 `{text, voice?}`）、`requirements.txt`（加 `edge-tts`）。
- [x] `Dockerfile.tts`（root；`git`+`build-essential`、CPU 版 `torch`+`torchaudio`、GitHub 安裝 MeloTTS、`unidic`/NLTK 語料）。
- [x] `backend/services/tts_client.py`（回 `(bytes, content_type)`、傳 voice）、`backend/routers/tts.py`（`POST /api/tts`，帶 voice）；`config.py` 加 `tts_base_url`。
- [x] 前端 `ChatPage`：🔊 播放鈕 + **語音下拉選單**；`api.ts` 加 `postBlob`。
- [x] `docker-compose.yaml`：`tts` service（`TTS_VOICE` 預設台女、`TTS_LANGUAGE=ZH` 供 fallback、HF 快取 volume；backend `TTS_BASE_URL` + `depends_on`）；`build.sh` 加 TTS image。

**M3 驗收**：選不同語音按 🔊 → 聽到對應男女聲/腔調；斷網時仍能用（自動離線 MeloTTS）。

> ⚠️ edge-tts 需 `tts` 容器可**連外網**；離線 fallback 需 MeloTTS 模型已在有網路時快取過（啟動預熱會下載）。

### ✅ M4 — 文字轉圖片（完成）

**決策**：**Stable Diffusion 1.5**（diffusers，OpenRAIL 可商用）；**自動偵測 GPU/CPU**（有 CUDA 用 GPU，否則 CPU）；
中文提示詞先用 **LLM 翻譯優化成英文**再生圖。

**流程**：輸入列按「生成圖片」→ `POST /api/image {prompt}` → `image_agent`：
`translate node`（LLM 中文→英文提示詞）→ `generate node`（呼叫 `image-service`）→ 回 `{prompt_en, image(base64 dataURL)}` → 前端顯示圖片 + 下載 + 可展開英文提示詞。

**已建檔案**
- [x] `image-service/`：`api.py`（FastAPI + diffusers SD1.5，`POST /generate` 回 PNG，埠 9003，自動 GPU/CPU）、`requirements.txt`。
- [x] `Dockerfile.image`（root；預設 CUDA 版 torch，GPU 修好即可用，沒 GPU 自動 CPU）。
- [x] `backend/services/image_client.py`、`agents/image_agent.py`、`routers/image.py`；`config.py` 加 `image_base_url`；掛進 `api.py`。
- [x] 前端 `ChatPage`：「生成圖片」鈕 + 圖片顯示/下載/英文提示詞。
- [x] `docker-compose.yaml` 加 `image` service（HF 模型快取 volume、GPU passthrough 註解備用；backend `IMAGE_BASE_URL` + `depends_on`）；`build.sh` 加 image image。

**M4 驗收**：輸入中文描述按「生成圖片」→ 得到一張圖（可下載、可看 LLM 產生的英文提示詞）。

> ⚠️ 最重的一關：SD image 很大、首次啟動下載模型(~4GB)；**CPU 生圖很慢**（一張數十秒~數分鐘）。GPU：修好主機 nvidia 驅動 + 裝 nvidia-container-toolkit + 取消 compose 的 `deploy.devices` 註解即可加速。

### ⏳ 其他（視需求）
- Skill 設計（`skill-design.md`）：把可重用能力（如 OCR 流程）包成 `backend/skills/<name>/SKILL.md`。
- DB：初期 SQLite，之後可無縫換 PostgreSQL（只改 `DATABASE_URL`）。

## 本機開發 / 部署指令（開發者自行執行）

```bash
# ── 後端（終端 1）──
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # 需要時調整 DATABASE_URL
python api.py                   # http://localhost:8000

# ── 前端（終端 2）──
cd frontend
npm install
npm run dev                     # http://localhost:5173（/api 由 Vite proxy 轉到 8000）

# ── OCR 服務（終端 3；要用圖片 OCR 才需要，M2）──
cd ocr-service
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # 較大，首次安裝與首次辨識會下載模型
python api.py                      # http://localhost:9001（backend dev 預設打這裡）

# ── TTS 服務（終端 4；要用語音朗讀才需要，M3）── MeloTTS，較重（PyTorch）
cd tts-service
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # 含 edge-tts（線上主用）
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu   # CPU 版（MeloTTS 離線 fallback 用）
pip install git+https://github.com/myshell-ai/MeloTTS.git            # MeloTTS 本體
python -m unidic download                                            # melo import 需要的字典
python api.py                      # http://localhost:9002；首次啟動預熱 MeloTTS（需網路）

# ── 文生圖服務（終端 5；要用文字生圖才需要，M4）── 很重（PyTorch + SD 模型）
cd image-service
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # 預設 CUDA 版 torch；純 CPU 想輕量可改裝 CPU 版 torch
python api.py                      # http://localhost:9003；首次啟動下載 SD1.5(~4GB)，自動用 GPU 或 CPU

# ── Docker 部署 ──
cp .env.example .env            # ★ 改 FRONTEND_PORT 等 ★
cp backend/.env.example backend/.env
set -a; . ./.env; set +a
docker network create "$NETWORK_NAME"   # 已存在就跳過
bash build.sh
docker-compose up -d
# 入口：http://<ip>:<FRONTEND_PORT>/multimodel/
```
