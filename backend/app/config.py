"""Application settings: the ONLY place environment variables are read.

Values come from the process environment, falling back to backend/.env (local, gitignored).
Secrets use SecretStr so they never appear in reprs, logs or tracebacks.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # YouCam integration. Mock mode is the safe default: no network, no units spent.
    youcam_mode: Literal["mock", "live"] = "mock"
    youcam_api_key: SecretStr | None = None
    youcam_base_url: str = "https://yce-api-01.makeupar.com"

    # Abuse and quota controls (used from Phase 1 onward).
    live_analysis_enabled: bool = False
    max_live_per_day: int = 25
    per_ip_per_day: int = 5
    credit_floor: int = 100

    # Web
    frontend_origin: str = "http://localhost:5173"
    currency: Literal["NGN", "USD"] = "NGN"

    @model_validator(mode="after")
    def _live_mode_needs_key(self) -> Settings:
        key = self.youcam_api_key.get_secret_value().strip() if self.youcam_api_key else ""
        if self.youcam_mode == "live" and not key:
            raise ValueError(
                "YOUCAM_MODE=live requires YOUCAM_API_KEY. The owner sets it in backend/.env "
                "(local) or Render environment variables (production)."
            )
        return self

    @property
    def cors_origins(self) -> list[str]:
        origins = {self.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"}
        return sorted(o for o in origins if o)


@lru_cache
def get_settings() -> Settings:
    return Settings()
