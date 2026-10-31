"""GlowCue API entry point.

Foundation stage: only /api/health exists. Feature routes are added in Phase 1
(see docs/prompts/02-backend-architecture.md).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import health


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="GlowCue API",
        version="0.1.0",
        description="Cosmetic skincare guidance powered by YouCam AI Skin Analysis. Not medical advice.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router, prefix="/api")
    return app


app = create_app()
