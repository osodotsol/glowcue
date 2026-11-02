from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe, also used by the landing page to wake the free-tier server."""
    return {"status": "ok", "mode": get_settings().youcam_mode}
