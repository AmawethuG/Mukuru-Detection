"""
Application configuration via Pydantic BaseSettings.
No FastAPI imports in this file.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite:///./mukuru.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    MOCK_SAFE_BROWSING: bool = True
    SAFE_BROWSING_API_KEY: str = ""
    LLM_ENABLED: bool = False
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    RULES_WEIGHT: float = 0.6
    CLASSIFIER_WEIGHT: float = 0.4
    CORS_ORIGINS: str = "http://localhost:5173"

    def cors_origins_list(self) -> list[str]:
        """Return CORS_ORIGINS as a list split on commas."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
