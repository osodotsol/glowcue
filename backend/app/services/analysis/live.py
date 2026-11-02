"""Live analysis: run the YouCam flow for one prepared photo and keep the outcome in a short-lived store.

The store holds scores and status only (never the photo) and forgets everything after 30 minutes. It lives in
process memory, so the API runs as a single worker (docs/ARCHITECTURE.md).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Protocol

from cachetools import TTLCache

from app.config import Settings
from app.models import AnalysisJob, ErrorDetail, NormalizedAnalysis
from app.services.image import PreparedImage
from app.services.limits import DailyLimiter
from app.services.normalize import SD_ACTIONS, build_live_analysis, normalise_items
from app.services.youcam_client import LiveCallRefused, OutputItem, YouCamClient, YouCamError
from app.services.youcam_errors import friendly_error

log = logging.getLogger("glowcue.analysis")

RESULT_TTL_S = 30 * 60


class SkinAnalyser(Protocol):
    async def analyse_skin(self, image: bytes, content_type: str, actions: tuple[str, ...]) -> list[OutputItem]: ...


ClientFactory = Callable[[Settings], AbstractAsyncContextManager[SkinAnalyser]]


def default_client_factory(settings: Settings) -> AbstractAsyncContextManager[SkinAnalyser]:
    return YouCamClient(settings)


class JobStore:
    def __init__(self, ttl_s: float = RESULT_TTL_S, maxsize: int = 1000) -> None:
        self._jobs: TTLCache[str, AnalysisJob] = TTLCache(maxsize=maxsize, ttl=ttl_s)

    def create(self) -> AnalysisJob:
        job = AnalysisJob(analysis_id=f"live-{uuid.uuid4()}", status="running")
        self._jobs[job.analysis_id] = job
        return job

    def get(self, analysis_id: str) -> AnalysisJob | None:
        return self._jobs.get(analysis_id)

    def succeed(self, analysis_id: str, analysis: NormalizedAnalysis) -> None:
        self._jobs[analysis_id] = AnalysisJob(analysis_id=analysis_id, status="success", analysis=analysis)

    def fail(self, analysis_id: str, error: ErrorDetail) -> None:
        self._jobs[analysis_id] = AnalysisJob(analysis_id=analysis_id, status="error", error=error)


async def run_live_analysis(
    *,
    analysis_id: str,
    image: PreparedImage,
    ip: str,
    settings: Settings,
    jobs: JobStore,
    limiter: DailyLimiter,
    client_factory: ClientFactory,
) -> None:
    """Background task: never raises. The outcome is written to `jobs`; the photo is dropped when this returns."""
    try:
        async with client_factory(settings) as client:
            items = await client.analyse_skin(image.data, image.content_type, SD_ACTIONS)
        normalised = normalise_items(items)
        if all(score is None for score in normalised.scores.values()):
            raise YouCamError("no_scores")
        jobs.succeed(analysis_id, build_live_analysis(analysis_id, normalised))
        missing = sorted(k for k, v in normalised.scores.items() if v is None)
        log.info("live analysis %s succeeded; not measured: %s", analysis_id, missing or "none")
    except YouCamError as exc:
        log.warning("live analysis %s failed: %s", analysis_id, exc.code)
        jobs.fail(analysis_id, friendly_error(exc.code))
        if not exc.units_possible:
            limiter.release(ip)  # YouCam bills successful tasks only, so a failed attempt gives the slot back
    except LiveCallRefused:
        log.warning("live analysis %s refused: live mode is not fully enabled", analysis_id)
        jobs.fail(analysis_id, friendly_error("auth_failed"))
        limiter.release(ip)
    except Exception:  # noqa: BLE001  (a background task must always record an outcome)
        log.exception("live analysis %s crashed", analysis_id)
        jobs.fail(analysis_id, friendly_error("unexpected"))
        limiter.release(ip)
