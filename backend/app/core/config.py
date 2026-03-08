"""Typed application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings with safe defaults for local development."""

    # App
    app_name: str = "SkillRank API"
    app_env: str = "dev"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Qdrant
    qdrant_url: str = ""
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "skills"
    qdrant_api_key: str = ""

    # Embeddings
    embed_model: str = "all-MiniLM-L6-v2"
    embed_dim: int = 384

    # Data
    skills_jsonl_path: str = "../skills_scraper/data/skills_raw.jsonl"

    # Search behavior
    default_top_k: int = 5
    max_top_k: int = 20
    qdrant_top_n: int = 50
    skip_startup_checks: bool = False
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def skills_jsonl_abspath(self) -> Path:
        """Return an absolute path to the skills JSONL source file."""
        path = Path(self.skills_jsonl_path)
        if path.is_absolute():
            return path
        return (BACKEND_ROOT / path).resolve()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
