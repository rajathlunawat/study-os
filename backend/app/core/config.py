"""
StudyOS Core — Configuration.

Centralised application settings loaded from environment variables / .env file.
Uses Pydantic BaseSettings for type validation and immutability.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    Values are loaded in this priority order (highest wins):
    1. Environment variables
    2. .env file
    3. Defaults defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "StudyOS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./studyos.db"

    # ── Vector Search ────────────────────────────────────────────
    FAISS_INDEX_DIR: str = "./data/faiss_indices"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ── Document Processing ──────────────────────────────────────
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── RAG ──────────────────────────────────────────────────────
    TOP_K_RESULTS: int = 5

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Derived helpers (not loaded from env) ────────────────────
    @property
    def max_upload_bytes(self) -> int:
        """Return MAX_UPLOAD_SIZE_MB converted to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def faiss_index_path(self) -> Path:
        """Return FAISS_INDEX_DIR as a resolved Path object."""
        return Path(self.FAISS_INDEX_DIR).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings.

    Using lru_cache ensures the .env file is read only once and the
    same Settings instance is reused throughout the application lifetime.
    """
    return Settings()
