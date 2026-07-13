"""集中設定物件（pydantic-settings）。程式各處只 import 這個 settings，不散落 os.getenv。
見 reference/backend/backend-conventions.md §5。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 資料庫（見 database.md）：初期 sqlite，之後換 postgres 只改這行
    database_url: str = "sqlite:///./data/app.db"

    app_env: str = "dev"  # dev / prod

    # 注意：LLM provider 走「前端設定頁註冊多個、存 DB」（llm-integration.md §5），
    # 故此處不放 LLM_PROVIDER / LLM_MODEL；由 services/llm_provider_service 從 DB 讀。

    # OCR 推論服務（獨立容器；M2）。dev 預設本機 9001，容器內由 compose 覆寫成 http://ocr:9001。
    ocr_base_url: str = "http://localhost:9001"

    # TTS 推論服務（獨立容器；M3）。dev 預設本機 9002，容器內由 compose 覆寫成 http://tts:9002。
    tts_base_url: str = "http://localhost:9002"

    # 文生圖推論服務（獨立容器；M4）。dev 預設本機 9003，容器內由 compose 覆寫成 http://image:9003。
    image_base_url: str = "http://localhost:9003"


settings = Settings()
