from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    postgres_dsn: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    postgres_dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
    return Settings(postgres_dsn=postgres_dsn)
