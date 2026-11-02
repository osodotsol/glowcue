"""GlowCue API entry point: app factory, CORS, routers and error handlers. No business logic here."""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.errors import install_error_handlers
from app.routes import analysis, health, shop
from app.services.analysis.live import JobStore, default_client_factory
from app.services.catalogue import get_catalogue
from app.services.image import MAX_CONCURRENT_PREPARATIONS
from app.services.limits import DailyLimiter
from app.services.youcam_client import live_refusal

log = logging.getLogger("glowcue")


def _log_startup(settings: Settings) -> None:
    """B4: what this server will do, without secrets (the key is reported only as present or absent)."""
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
        log.propagate = False
    refusal = live_refusal(settings)
    log.info(
        "GlowCue API: YOUCAM_MODE=%s, LIVE_ANALYSIS_ENABLED=%s, API key %s -> live analysis %s",
        settings.youcam_mode,
        settings.live_analysis_enabled,
        "present" if settings.has_api_key else "absent",
        "ON" if refusal is None else f"OFF ({refusal})",
    )


def create_app() -> FastAPI:
    settings = get_settings()
    get_catalogue()  # validate the catalogue at startup: fail fast on bad data
    app = FastAPI(
        title="GlowCue API",
        version="0.2.0",
        description="Cosmetic skincare discovery and shopping assistant. Not medical advice.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    install_error_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(shop.router, prefix="/api")
    app.include_router(analysis.router, prefix="/api")
    # Per-process state for live analysis (single worker). Tests replace youcam_factory with a fake transport.
    app.state.jobs = JobStore()
    app.state.limiter = DailyLimiter()
    app.state.youcam_factory = default_client_factory
    app.state.image_slots = asyncio.Semaphore(MAX_CONCURRENT_PREPARATIONS)
    _log_startup(settings)
    return app


app = create_app()
