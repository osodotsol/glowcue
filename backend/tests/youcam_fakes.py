"""A fake YouCam API for tests (httpx.MockTransport). It never touches the network and never sees a real key."""

from __future__ import annotations

import copy
import io
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

from app.config import Settings
from app.services.youcam_client import CREDIT_PATH, DELETE_PATH, FILE_PATH, TASK_PATHS, YouCamClient

FAKE_KEY = "placeholder-key-for-tests"
UPLOAD_HOST = "uploads.example.test"
FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "youcam_sd_success.json").read_text(encoding="utf-8"))


def live_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "youcam_mode": "live",
        "live_analysis_enabled": True,
        "youcam_api_key": FAKE_KEY,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def selfie_bytes(size: tuple[int, int] = (640, 800), fmt: str = "JPEG", **save: Any) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (190, 140, 120)).save(buf, format=fmt, **save)
    return buf.getvalue()


class FakeYouCam:
    """Answers the documented endpoints. Tweak behaviour through the attributes before use."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.balance: float = 1000
        self.statuses: list[str] = ["running", "success"]  # poll answers in order (the last one repeats)
        self.task_error: str | None = None
        self.result: dict[str, Any] = copy.deepcopy(FIXTURE["data"])
        self.presigned_url = f"https://{UPLOAD_HOST}/put/object-1"
        self.overrides: dict[tuple[str, str], Callable[[httpx.Request], httpx.Response]] = {}
        self._polls = 0

    # convenience views ------------------------------------------------------------------------------
    def calls(self, method: str, path: str) -> list[httpx.Request]:
        return [r for r in self.requests if r.method == method and r.url.path == path]

    @property
    def youcam_requests(self) -> list[httpx.Request]:
        return [r for r in self.requests if r.url.host != UPLOAD_HOST]

    @property
    def uploads(self) -> list[httpx.Request]:
        return [r for r in self.requests if r.url.host == UPLOAD_HOST]

    # transport --------------------------------------------------------------------------------------
    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        key = (request.method, request.url.path)
        if key in self.overrides:
            return self.overrides[key](request)
        if request.url.host == UPLOAD_HOST:
            return httpx.Response(200)
        path = request.url.path
        if key == ("GET", CREDIT_PATH):
            return httpx.Response(
                200,
                json={
                    "status": 200,
                    "results": [
                        {
                            "id": 1,
                            "type": "ApiPaygToken",
                            "amount": int(self.balance),
                            "amount_dec": float(self.balance),
                            "expiry": 1900000000000,
                        }
                    ],
                },
            )
        if key == ("POST", FILE_PATH):
            spec = json.loads(request.content)["files"][0]
            put = {
                "method": "PUT",
                "url": self.presigned_url,
                "headers": {"Content-Type": spec["content_type"], "Content-Length": str(spec["file_size"])},
            }
            files = [{**spec, "file_id": "file-123", "requests": [put]}]
            return httpx.Response(200, json={"status": 200, "data": {"files": files}})
        if request.method == "POST" and path in TASK_PATHS.values():
            return httpx.Response(200, json={"status": 200, "data": {"task_id": "task-123"}})
        if request.method == "GET" and any(path == f"{p}/task-123" for p in TASK_PATHS.values()):
            status = self.statuses[min(self._polls, len(self.statuses) - 1)]
            self._polls += 1
            if status == "success" and self.task_error is None:
                return httpx.Response(200, json={"status": 200, "data": self.result})
            if status == "success":  # an error outcome
                body = {"task_status": "error", "error": self.task_error, "error_message": "x"}
                return httpx.Response(200, json={"status": 200, "data": body})
            return httpx.Response(200, json={"status": 200, "data": {"task_status": status}})
        if key == ("POST", DELETE_PATH):
            return httpx.Response(200, json={"status": 200})
        return httpx.Response(404, json={"status": 404, "error": "not found"})


class Clock:
    """Fake time: `sleep` advances `now` and records every requested pause."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(settings: Settings, fake: FakeYouCam, clock: Clock | None = None) -> YouCamClient:
    clock = clock or Clock()
    return YouCamClient(settings, transport=httpx.MockTransport(fake), sleep=clock.sleep, clock=clock.time)
