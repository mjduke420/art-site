"""Application configuration, loaded from environment / .env file.

All secrets and tunables come from the environment so nothing sensitive is
hardcoded. See .env.example for the full list.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Image formats we accept on upload. Keys are normalized Pillow format names.
ALLOWED_IMAGE_FORMATS: dict[str, str] = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
}

DEFAULT_SECRET = "change-me-to-a-long-random-string"
DEFAULT_PASSWORD = "change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    site_title: str = "Portfolio"
    secret_key: str = DEFAULT_SECRET
    admin_username: str = "admin"
    admin_password: str = DEFAULT_PASSWORD
    data_dir: Path = Path("data")
    max_upload_mb: int = 25
    thumbnail_max_px: int = 800

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "portfolio.db"

    @property
    def database_url(self) -> str:
        # Forward slashes work for SQLite URLs on every platform.
        return f"sqlite:///{self.db_path.as_posix()}"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def uses_insecure_defaults(self) -> bool:
        return self.secret_key == DEFAULT_SECRET or self.admin_password == DEFAULT_PASSWORD


@lru_cache
def get_settings() -> Settings:
    return Settings()
