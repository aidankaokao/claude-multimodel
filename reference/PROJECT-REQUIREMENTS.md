# 專案需求說明（開發者填寫）

> **用法**：開新專案時複製這份到 `reference/PROJECT-REQUIREMENTS.md` 並填寫。
> 新的 Claude Code session 會先讀根目錄 `CLAUDE.md` + 這份需求 + `reference/` 慣例，再開工。
> 勾選用 `[x]`；不確定的留白，session 會在開工前一次問你。

---

## 1. 專案基本

- **專案名稱**：multimodel
- **APP_ROUTE（路由名稱，內外網共用；見 deploy-guide 路由機制）**：例 `myapp`
- **一句話目標**：多模態問答界面，使用開源方式與模型建構各種多模態交互的問答界面，例如文字轉語音、文字轉圖片、圖片OCR等，以教學方式來帶領我建立，從簡單到困難

## 2. 前端

- [x] 需要前端
- [ ] 不需要前端（純後端 / API / CLI）
- 若需要，**視覺風格三選一**（見 `reference/frontend/frontend-style-*.md`）：
  - [ ] Formal（乾淨後台 SaaS）
  - [ ] Glass Wave（淡藍紫玻璃波）
  - [x] Aurora Glass（極光琉璃，可切主題盤）
- **主要頁面 / 功能**：前端交互操作界面

## 3. 後端

- [x] 需要後端 API（FastAPI，見 `reference/backend/backend-conventions.md`）
- **主要 API / 功能**：前後端交互等，依需求構建

## 4. AI Agent

- [x] 需要 AI agent（LangGraph，見 `reference/backend/langgraph-agent.md`）
- **流程 / 說明**：問答依需求構建可判斷多模態需求

## 5. LLM

- [x] 需要用到 LLM（見 `reference/backend/llm-integration.md`）
- provider：[x] 本地 Ollama　[x] 外部 OpenAI　[x] 本地 vLLM
- 設定來源：[x] 前端設定頁註冊多個（有前端建議）　[ ] `.env`（無前端）
- **模型**：各種多模態模型構建

## 6. 資料庫

- [x] 需要資料庫（SQLAlchemy Core，見 `reference/backend/database.md`）
- 初期 [x] SQLite　→ 之後 [ ] PostgreSQL
- **主要資料表 / 實體**：不確定是否需要，依需求建立

## 7. Skill

- [x] 需要設計 skill（`SKILL.md`，見 `reference/backend/skill-design.md`）
- **說明**：不確定是否需要，依需求建立

## 8. 部署

- [x] 現在就要 Docker 部署（見 `reference/deploy/deploy-guide.md`）
- **IMAGE_PREFIX**（image 命名前綴，通常＝專案名）：multimodel
- 前端對外埠 **FRONTEND_PORT**：在.env讓我進行設定
- 內網訪問：`http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/`
- 之後綁 DNS（團隊 nginx）：`https://<DNS>/<APP_ROUTE>/`

## 9. 其他需求 / 注意事項（自由填寫）

- 只能使用開源或免費的套件，不可使用商業或付費套件。
- 你不可以幫我執行程式，只能修改程式，若要執行請直接給我命令，我自己執行。
- 每次修改完程式請自動更新CLAUDE.md。
- 盡可能保持CLAUDE.md簡潔(盡可能不要超過500行)，若有關於專案細節請另外填寫開發計劃書或其他相關文件，並在CLAUDE.md中提示閱讀即可。
