"""Centralne ustawienia - czyta .env, ladowane raz przy starcie."""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
PROMPTS_DIR = CONFIG_DIR / "prompts"
DATA_DIR = REPO_ROOT / "data"
SCRIPTS_DIR = REPO_ROOT / "scripts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    youtube_api_key: str = Field(default="", alias="YOUTUBE_API_KEY")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    scripts_per_day: int = Field(default=3, alias="SCRIPTS_PER_DAY")
    debug: bool = Field(default=False, alias="DEBUG")

    # Channel scraping (Faza 1.5): expand channel URLs -> top shorts by views.
    channel_min_views: int = Field(default=500_000, alias="CHANNEL_MIN_VIEWS")
    channel_max_shorts_per_channel: int = Field(default=10, alias="CHANNEL_MAX_SHORTS_PER_CHANNEL")
    channel_scan_depth: int = Field(default=30, alias="CHANNEL_SCAN_DEPTH")

    def has_llm(self) -> bool:
        return bool(self.gemini_api_key or self.groq_api_key)

    def has_telegram(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


settings = Settings()
