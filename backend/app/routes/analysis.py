"""Live skin analysis: submit a selfie, then poll for the result. Thin handlers only.

POST /api/analyses?consent=true   body = the photo itself (Content-Type image/jpeg or image/png)
GET  /api/analyses/{analysis_id}  running | success (+ analysis) | error (+ friendly error)

The photo is sent as the raw request body, not multipart: Starlette spools multipart uploads over 1 MB to a
temporary file on disk, and photos must stay in memory. The body is read with a hard 10 MB cap.

Order of work in POST (cheapest first, so abuse costs as little as possible):
  1. live mode on, consent given, declared type and size     (no body read)
  2. body read with the 10 MB cap; size and file signature   (no decoding)
  3. reserve daily capacity (per IP and global)              (atomic: no await between check and increment)
  4. decode and re-encode in a worker thread, at most MAX_CONCURRENT_PREPARATIONS at once
  Any failure after step 3, including a cancelled request, releases the reservation, so slots never get stuck.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Query, Request
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.errors import AppError
from app.models import AnalysisJob
from app.services.analysis.live import run_live_analysis
from app.services.image import MAX_UPLOAD_BYTES, PreparedImage, check_upload, prepare_image
from app.services.youcam_client import live_refusal

router = APIRouter()

ACCEPTED_TYPES = {"image/jpeg", "image/png"}


async def _read_capped(request: Request) -> bytes:
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES:
        raise AppError("image_too_large", "That photo is over 10 MB. Please choose a smaller one.", status=413)
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise AppError("image_too_large", "That photo is over 10 MB. Please choose a smaller one.", status=413)
        chunks.append(chunk)
    return b"".join(chunks)


async def _prepare_off_loop(request: Request, data: bytes) -> PreparedImage:
    """Decode in a worker thread so the event loop keeps serving; refuse instead of queueing when saturated."""
    slots: asyncio.Semaphore = request.app.state.image_slots
    if slots.locked():  # no await between this check and the acquire below
        raise AppError(
            "busy",
            "We're preparing other photos right now. Please try again in a moment.",
            status=503,
            retryable=True,
        )
    async with slots:
        return await run_in_threadpool(prepare_image, data)


@router.post("/analyses", status_code=202, tags=["analysis"])
async def start_live_analysis(
    request: Request,
    background: BackgroundTasks,
    consent: bool = Query(default=False, description="Must be true: the customer agreed to send the photo."),
) -> AnalysisJob:
    """Accept one selfie for live cosmetic analysis by YouCam. Returns immediately with an id to poll."""
    settings = get_settings()
    if live_refusal(settings) is not None:
        raise AppError(
            "live_unavailable",
            "Live analysis isn't switched on. You can choose a sample profile instead.",
            status=503,
        )
    if not consent:  # checked before the photo is read
        raise AppError(
            "consent_required",
            "Please confirm you agree to send your photo for analysis before we can analyse it.",
            status=422,
        )
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type not in ACCEPTED_TYPES:
        raise AppError("invalid_image", "Please choose a JPEG or PNG photo.", status=415)

    data = await _read_capped(request)
    check_upload(data)  # size and signature only: nothing is decoded before capacity is reserved

    ip = request.client.host if request.client else "unknown"
    limiter = request.app.state.limiter
    limiter.reserve(ip, per_ip_max=settings.per_ip_per_day, global_max=settings.max_live_per_day)
    try:
        image = await _prepare_off_loop(request, data)
    except BaseException:  # invalid image, busy, or the request was cancelled: give the slot back
        limiter.release(ip)
        raise
    del data

    jobs = request.app.state.jobs
    job = jobs.create()
    background.add_task(
        run_live_analysis,
        analysis_id=job.analysis_id,
        image=image,
        ip=ip,
        settings=settings,
        jobs=jobs,
        limiter=limiter,
        client_factory=request.app.state.youcam_factory,
    )
    return job


@router.get("/analyses/{analysis_id}", tags=["analysis"])
async def live_analysis_status(analysis_id: str, request: Request) -> AnalysisJob:
    job = request.app.state.jobs.get(analysis_id)
    if job is None:
        raise AppError("unknown_analysis", "This analysis has expired or does not exist. Please start again.", 404)
    return job
