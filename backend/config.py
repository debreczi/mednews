from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI (LLM enrichment)
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "gpt-5.4-mini"

    # Scraping
    relevance_threshold: float = 6.0

    # Twitter / X API
    twitter_bearer_token: str = ""

    # Database
    db_path: str = "./mednews.db"

    # Admin
    admin_api_key: str = "change_me"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Frontend API URL (used by Vite, not Python)
    vite_api_base_url: str = "http://localhost:8000"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
