"""Application settings: the ONLY place environment variables are read.

Sources, highest priority first (security rule B1, docs/SECURITY_PRIVACY.md 4.4):
  1. values passed to Settings(...) directly (tests),
  2. backend/.env (local, gitignored, owner-edited),
  3. process environment variables (Render in production, where there is no .env file).
backend/.env outranks the environment so a command cannot switch a local server to live mode with
`YOUCAM_MODE=live ...`; only the owner, who edits .env, can.

Secrets use SecretStr so they never appear in reprs, logs or tracebacks. The YouCam host is not configurable:
it lives in app/services/youcam/client.py only, so the key can never be sent to a configured lookalike host.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEV_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


def _is_local_origin(origin: str) -> bool:
    host = origin.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0].lower()
    return host in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]", "")  # noqa: S104 (compared, not bound)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # YouCam integration. Mock mode is the safe default: no network, no units spent.
    youcam_mode: Literal["mock", "live"] = "mock"
    youcam_api_key: SecretStr | None = None
    # Which task API version to call. v2.1 is documented, but the docs only show the v2.0 File API next to it;
    # if the first approved probe shows v2.1 rejects a v2.0 file id, the owner can switch to "v2.0" here.
    youcam_task_api: Literal["v2.1", "v2.0"] = "v2.1"
    youcam_poll_interval_s: float = Field(default=10.0, ge=2.0, le=60.0)
    youcam_task_timeout_s: float = Field(default=180.0, ge=20.0, le=900.0)

    # Abuse and quota controls. Live analysis stays off unless the owner switches it on (rule B6).
    live_analysis_enabled: bool = False
    max_live_per_day: int = Field(default=25, ge=0)
    per_ip_per_day: int = Field(default=5, ge=0)
    credit_floor: int = Field(default=100, ge=0)  # 0 disables the balance check

    # Web. In production only FRONTEND_ORIGIN may call the API; local dev origins are added only in development.
    app_env: Literal["development", "production"] = "development"
    frontend_origin: str = "http://localhost:5173"
    currency: Literal["NGN", "USD"] = "NGN"
    budget_default: int = 30000

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # B1: backend/.env before process environment variables (see module docstring).
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    @model_validator(mode="after")
    def _production_needs_real_origin(self) -> Settings:
        if self.app_env == "production" and _is_local_origin(self.frontend_origin):
            raise ValueError(
                "APP_ENV=production requires FRONTEND_ORIGIN to be the deployed frontend's URL, "
                "not a localhost address."
            )
        return self

    @model_validator(mode="after")
    def _live_mode_needs_key(self) -> Settings:
        if self.youcam_mode == "live" and not self.has_api_key:
            raise ValueError(
                "YOUCAM_MODE=live requires YOUCAM_API_KEY. The owner sets it in backend/.env "
                "(local) or Render environment variables (production)."
            )
        return self

    @property
    def has_api_key(self) -> bool:
        return bool(self.youcam_api_key and self.youcam_api_key.get_secret_value().strip())

    @property
    def cors_origins(self) -> list[str]:
        origins = {self.frontend_origin}
        if self.app_env == "development":
            origins |= set(DEV_ORIGINS)
        return sorted(o for o in origins if o)


@lru_cache
def get_settings() -> Settings:
    return Settings()
