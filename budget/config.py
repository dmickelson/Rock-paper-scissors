from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_credentials_file: Path = Path.home() / ".config" / "budget" / "credentials.json"
    google_token_file: Path = Path.home() / ".config" / "budget" / "token.json"
    budget_spreadsheet_id: str = ""
    gmail_lookback_days: int = 7
    dedup_window_days: int = 3
    default_timezone: str = "America/New_York"


settings = Settings()
