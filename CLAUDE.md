# multimodel — 專案開發指引（入口）

多模態問答界面：用**開源方式與模型**建構各種多模態交互（文字轉語音、文字轉圖片、圖片 OCR…），
**以教學方式、從簡單到困難**逐步建立。

> **動工前依序讀：**
> 1. `reference/PROJECT-REQUIREMENTS.md` — 本專案需求（開發者已填）。
> 2. `DEVELOPMENT-PLAN.md` — **開發計劃書**（架構、里程碑、決策、指令；細節都在這）。
> 3. 下方對應的 `reference/` 慣例文件。
>
> **一律照 `reference/` 慣例做，不要自行發明架構或風格；需求以 `PROJECT-REQUIREMENTS.md` 為準；有衝突先問開發者。**

## 已確認的關鍵決策（詳見 DEVELOPMENT-PLAN.md）

| 面向 | 決定 | 慣例文件 |
|---|---|---|
| 前端風格 | Aurora Glass（極光琉璃，可切主題盤）| `reference/frontend/frontend-style-aurora-glass.md` |
| 前後端接線 | 同源 `/api`，dev Vite proxy／prod nginx 反代 | `reference/frontend/frontend-backend-integration.md` |
| 後端 | FastAPI，`python api.py` port 8000 | `reference/backend/backend-conventions.md` |
| AI agent | LangGraph `StateGraph` | `reference/backend/langgraph-agent.md` |
| LLM | `get_chat_model()` 工廠；provider 在**設定頁註冊多筆、存 DB** | `reference/backend/llm-integration.md`（§5）|
| 資料庫 | SQLAlchemy Core，初期 SQLite | `reference/backend/database.md` |
| 多模態模型 | **各自獨立推論服務（多容器）**，backend 以 HTTP 呼叫；只用開源/免費 | 見 DEVELOPMENT-PLAN.md 架構 |
| Skill | `SKILL.md`（需要時）| `reference/backend/skill-design.md` |
| 部署 | Docker Compose，`APP_ROUTE=multimodel` | `reference/deploy/deploy-guide.md` |

## 目前進度

- **✅ M1**：文字問答打底 + LLM Provider 設定頁（全鏈路跑通）；問答支援**串流逐字輸出**（`/api/chat/stream`）與**Markdown 渲染**。
- **✅ M2**：圖片 OCR（PaddleOCR 繁中，獨立容器 `ocr-service/`）→ `/api/ocr` → `ocr_agent`（辨識後自動交 LLM 整理）；前端聊天頁可上傳圖片。
- **✅ M3**：文字轉語音（獨立容器 `tts-service/`，**混合：線上 edge-tts 為主 + 離線 MeloTTS 備援**）→ `/api/tts`；前端 🔊 播放鈕 + 語音可切（台/陸、男/女）。
- **✅ M4**：文字轉圖片（獨立容器 `image-service/`，**SD 1.5，自動 GPU/CPU**）→ `/api/image`；`image_agent` 先用 LLM 把中文提示詞翻成英文再生圖；前端「生成圖片」鈕。
- **四種多模態皆完成**。後續見 `DEVELOPMENT-PLAN.md` 的增強 backlog。
- **進度／To-Do 清單**：見 `DEVELOPMENT-PLAN.md` 的「進度總覽（To-Do）」段（勾選狀態即進度）。

## 專案結構（重點）

```
backend/     FastAPI + LangGraph + SQLAlchemy Core（api.py / config.py / db / services / llm / agents / routers）
frontend/    Vite + React + TS，Aurora Glass（src/{lib,stores,components,pages}）
ocr-service/   獨立 OCR 推論服務（FastAPI + PaddleOCR，埠 9001；M2）
tts-service/   獨立 TTS 推論服務（FastAPI + edge-tts/MeloTTS，埠 9002；M3）
image-service/ 獨立文生圖服務（FastAPI + diffusers SD1.5，埠 9003；M4）
reference/     開發慣例（唯一真理來源，勿改）
根目錄         docker-compose.yaml / Dockerfile.*（backend/frontend/ocr/tts/image）/ build.sh / .env(.example)
DEVELOPMENT-PLAN.md  架構、里程碑、開發/部署指令
```

## 開發者工作約定（務必遵守）

- **只能用開源或免費套件 / 模型**，不可用商業或付費套件。
- **不要幫開發者執行程式**：只改程式；要執行時**直接給指令**讓開發者自己跑（見 DEVELOPMENT-PLAN.md 指令段）。
- **每次改完程式**：同步更新本 `CLAUDE.md`（進度）與需要時的 `DEVELOPMENT-PLAN.md`。
- **保持本檔精簡**（<500 行）：專案細節寫進 `DEVELOPMENT-PLAN.md` 或其他文件，這裡只留入口與索引。
