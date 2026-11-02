"""The ONLY module that talks to YouCam (security rule B2, docs/SECURITY_PRIVACY.md 4.4). I/O only.

Flow (docs/YOUCAM_API.md 6.1, official docs: docs.perfectcorp.com/reference/ai_skin_analysis):
  1. POST /s2s/v2.0/file                  register the upload, get file_id + a presigned PUT request
  2. PUT  <presigned url>                  raw bytes with EXACTLY the returned headers (no Authorization)
  3. POST /s2s/{v2.1|v2.0}/task/skin-analysis   format="json", SD actions only, no mask overlay
  4. GET  .../task/skin-analysis/{task_id} polled every ~10 s until success or error
  5. POST /s2s/v2.0/task/delete            removes the task, its input file and outputs (best effort)

Safeguards:
  * Every request goes through `_send`, which refuses unless YOUCAM_MODE=live AND LIVE_ANALYSIS_ENABLED AND a
    key is configured (B2). When those are not all true the client is built with a transport that raises on
    any request, so nothing can reach the network even by mistake (B3).
  * Only idempotent reads (GET) are retried, on 429/5xx/network errors, at most twice with backoff and jitter.
    Task creation is never retried: a retry could start (and bill) a second analysis.
  * Before any upload the unit balance is read (free) and the run is refused below CREDIT_FLOOR.
  * Logs carry step names and HTTP status codes only: never the key, Authorization header, presigned or
    result URLs, file/task ids, image bytes or response bodies.

Unverified behaviour is isolated here and listed in UNVERIFIED for the first owner-approved probe.
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
import re
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.config import Settings

log = logging.getLogger("glowcue.youcam")
# httpx and httpcore log every request URL at INFO/DEBUG, which would expose presigned upload URLs and task ids.
for _noisy in ("httpx", "httpcore"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

YOUCAM_BASE_URL = "https://yce-api-01.makeupar.com"
FILE_PATH = "/s2s/v2.0/file"
TASK_PATHS = {"v2.1": "/s2s/v2.1/task/skin-analysis", "v2.0": "/s2s/v2.0/task/skin-analysis"}
DELETE_PATH = "/s2s/v2.0/task/delete"
CREDIT_PATH = "/s2s/v1.0/client/credit"

# Official unit table: 9-12 SD concerns cost 14 units, charged only when a task succeeds.
UNITS_PER_ANALYSIS = 14
MAX_READ_RETRIES = 2
TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# Assumptions the docs do not settle; each one is checked during the first approved live probe.
UNVERIFIED = ("the credit response still has the 'results' shape recorded on 31 Oct 2026 (see parse_balance)",)


class LiveCallRefused(RuntimeError):  # noqa: N818  (reads better than "...Error" in logs and tests)
    """A YouCam request was attempted while live analysis is not fully enabled."""


class YouCamError(Exception):
    """A failed YouCam step. `code` is YouCam's error code when it gave one, otherwise a GlowCue code."""

    def __init__(
        self,
        code: str,
        *,
        http_status: int | None = None,
        units_possible: bool = False,
        diagnostic: str | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        # True when a task may have been created and could still be billed (e.g. we timed out while it ran).
        self.units_possible = units_possible
        # Structure-only description of an unrecognised response (describe_shape): no values, ids or URLs.
        self.diagnostic = diagnostic


# ------------------------------------------------------------------------------------- balance parsing
class _NotJson:
    """Stands in for a 2xx body that is not JSON; only its length is ever reported."""

    def __init__(self, size: int) -> None:
        self.size = size


_SAFE_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,39}$")
_MAX_DEPTH = 6
_MAX_KEYS = 20
_MAX_SHAPE_CHARS = 600


def describe_shape(value: Any, _depth: int = 0) -> str:
    """The STRUCTURE of a JSON value for diagnostics: object keys, nesting and value types, never the values.

    Keys that do not look like ordinary field names (long, or containing URL or id characters) are shown as
    <key>, in case a response is keyed by data. Arrays list the distinct shapes of their first few elements.
    """
    if _depth == 0:
        text = describe_shape(value, 1)
        return text if len(text) <= _MAX_SHAPE_CHARS else text[: _MAX_SHAPE_CHARS - 3] + "..."
    if isinstance(value, _NotJson):
        return f"non-JSON body ({value.size} bytes)"
    if _depth > _MAX_DEPTH:
        return "..."
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        kinds = sorted({describe_shape(item, _depth + 1) for item in value[:5]})
        return f"array[{' | '.join(kinds)}]"
    if isinstance(value, dict):
        fields = []
        for key in sorted(value, key=str)[:_MAX_KEYS]:
            name = key if isinstance(key, str) and _SAFE_KEY.match(key) else "<key>"
            fields.append(f"{name}:{describe_shape(value[key], _depth + 1)}")
        more = ", ..." if len(value) > _MAX_KEYS else ""
        return "object{" + ", ".join(fields) + more + "}"
    return "other"


def parse_balance(body: Any) -> float | None:
    """Total units from the balance response, or None when the shape is not the verified one.

    Verified shape (the response recorded on 31 Oct 2026, docs/YOUCAM_API.md 6.8) - no `data` wrapper:
        {"status": int, "results": [{"id": int, "type": str, "amount": int, "amount_dec": float, "expiry": int}]}
    The unit-system docs say the endpoint shows units "to two decimal places", which is `amount_dec`; the integer
    `amount` is used only when `amount_dec` is absent. Several entries (unit batches) are summed. Anything else,
    including a wrong type anywhere in an entry, returns None so the caller fails closed.
    """
    if not isinstance(body, dict):
        return None
    entries = body.get("results")
    if not isinstance(entries, list) or not entries:
        return None
    total = 0.0
    for entry in entries:
        if not isinstance(entry, dict):
            return None
        value = entry["amount_dec"] if "amount_dec" in entry else entry.get("amount")
        if isinstance(value, bool) or not isinstance(value, int | float):
            return None
        if not math.isfinite(value) or value < 0:
            return None
        total += float(value)
    return total


# ------------------------------------------------------------------------------------- response shapes
class _Loose(BaseModel):
    model_config = ConfigDict(extra="ignore")


class PresignedRequest(_Loose):
    method: str = "PUT"
    url: str
    headers: dict[str, str] = {}


class RegisteredFile(_Loose):
    file_id: str
    requests: list[PresignedRequest]


class OutputItem(_Loose):
    """One entry of data.results.output[] (format="json"). Unknown extra fields are ignored."""

    type: str
    region: str | None = None
    raw_score: float | None = None
    ui_score: float | None = None
    score: float | None = None


class TaskState(_Loose):
    task_status: str
    error: str | None = None
    results: dict[str, Any] | None = None


def live_refusal(settings: Settings) -> str | None:
    """Why live calls are not allowed right now, or None when they are."""
    if settings.youcam_mode != "live":
        return "YOUCAM_MODE is not 'live'"
    if not settings.live_analysis_enabled:
        return "LIVE_ANALYSIS_ENABLED is off"
    if not settings.has_api_key:
        return "no YouCam API key is configured"
    return None


class _RefusingTransport(httpx.AsyncBaseTransport):
    """Used whenever live calls are not allowed (B3): any request fails before touching the network."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        raise LiveCallRefused("YouCam requests are disabled (mock mode or live analysis switched off)")


class YouCamClient:
    """Async YouCam client. Use as `async with YouCamClient(settings) as client: ...`."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        # The last successful task's `data` object, kept in memory for the owner-approved probe script only.
        self.last_result: dict[str, Any] | None = None
        self._sleep = sleep
        self._clock = clock
        if live_refusal(settings) is not None:
            transport = _RefusingTransport()  # B3: never a real transport outside live mode
        self._http = httpx.AsyncClient(
            transport=transport or httpx.AsyncHTTPTransport(),
            timeout=TIMEOUT,
            follow_redirects=False,
        )

    async def __aenter__(self) -> YouCamClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------------------ the choke point (B2)
    async def _send(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
        authorise: bool = True,
    ) -> httpx.Response:
        reason = live_refusal(self._settings)
        if reason is not None:
            raise LiveCallRefused(reason)
        send_headers = dict(headers or {})
        if authorise:
            key = self._settings.youcam_api_key.get_secret_value().strip()  # type: ignore[union-attr]
            send_headers["Authorization"] = f"Bearer {key}"
        attempts = 1 + (MAX_READ_RETRIES if method == "GET" else 0)  # only idempotent reads are retried
        for attempt in range(attempts):
            last = attempt == attempts - 1
            try:
                response = await self._http.request(method, url, json=json, content=content, headers=send_headers)
            except httpx.TimeoutException:
                if last:
                    raise YouCamError("timeout", units_possible=method == "POST") from None
            except httpx.HTTPError:
                if last:
                    raise YouCamError("network") from None
            else:
                if not last and (response.status_code == 429 or response.status_code >= 500):
                    log.info("YouCam %s returned %s; retrying", method, response.status_code)
                else:
                    return response
            await self._sleep(min(8.0, 2.0**attempt) + random.uniform(0, 0.5))  # noqa: S311 (jitter, not crypto)
        raise YouCamError("network")  # unreachable: the loop returns or raises on its last attempt

    @staticmethod
    def _data(response: httpx.Response, step: str) -> Any:
        """Return body["data"] for a 2xx JSON response, else raise a YouCamError with the best code we have."""
        body: Any = None
        try:
            body = response.json()
        except ValueError:
            body = None
        if response.is_success and isinstance(body, dict) and "data" in body:
            return body["data"]
        code = body.get("error_code") if isinstance(body, dict) else None
        if response.status_code == 401:
            code = "auth_failed"
        elif response.status_code == 429:
            code = "rate_limited"
        log.warning("YouCam %s failed: HTTP %s (%s)", step, response.status_code, code or "no error code")
        raise YouCamError(code or ("bad_response" if response.is_success else f"http_{response.status_code}"),
                          http_status=response.status_code)  # fmt: skip

    # ------------------------------------------------------------------------------------- operations
    async def credit_balance(self) -> float:
        """Total unit balance. Unlike the task endpoints, this response has no `data` wrapper (see parse_balance)."""
        response = await self._send("GET", f"{YOUCAM_BASE_URL}{CREDIT_PATH}")
        if not response.is_success:
            self._data(response, "credit")  # raises the mapped error: auth_failed, rate_limited, http_<status>
        try:
            body: Any = response.json()
        except ValueError:
            body = _NotJson(len(response.content))
        balance = parse_balance(body)
        if balance is None:
            shape = describe_shape(body)
            # Structure only (key names and value types): never values, ids, URLs, headers or the key.
            log.warning("YouCam credit: balance response not recognised; structure: %s", shape)
            raise YouCamError("credit_unknown", http_status=response.status_code, diagnostic=shape)
        return balance

    async def _ensure_credit_floor(self) -> None:
        floor = self._settings.credit_floor
        if floor <= 0:
            return
        balance = await self.credit_balance()
        if balance - UNITS_PER_ANALYSIS < floor:
            log.warning("YouCam: balance at the credit floor; live analysis paused")
            raise YouCamError("credit_floor")

    async def _register_and_upload(self, image: bytes, content_type: str) -> str:
        payload = {"files": [{"content_type": content_type, "file_name": "selfie.jpg", "file_size": len(image)}]}
        data = self._data(await self._send("POST", f"{YOUCAM_BASE_URL}{FILE_PATH}", json=payload), "file")
        try:
            registered = RegisteredFile.model_validate(data["files"][0])
            put = registered.requests[0]
        except (KeyError, IndexError, TypeError, ValidationError):
            raise YouCamError("bad_response") from None
        if put.method.upper() != "PUT" or not put.url.startswith("https://"):
            raise YouCamError("bad_response")
        # Exactly the returned headers; never the Authorization header (the URL is a third-party storage host).
        response = await self._send("PUT", put.url, content=image, headers=put.headers, authorise=False)
        if not response.is_success:
            log.warning("YouCam upload failed: HTTP %s", response.status_code)
            raise YouCamError("upload_failed", http_status=response.status_code)
        return registered.file_id

    async def _create_task(self, file_id: str, actions: Sequence[str]) -> str:
        payload = {
            "src_file_id": file_id,
            "dst_actions": list(actions),
            "miniserver_args": {"enable_mask_overlay": False},
            "format": "json",  # the documented default is "zip"
        }
        path = TASK_PATHS[self._settings.youcam_task_api]
        data = self._data(await self._send("POST", f"{YOUCAM_BASE_URL}{path}", json=payload), "task")
        task_id = data.get("task_id") if isinstance(data, dict) else None
        if not isinstance(task_id, str) or not task_id:
            raise YouCamError("bad_response", units_possible=True)
        return task_id

    async def _poll(self, task_id: str) -> list[OutputItem]:
        path = TASK_PATHS[self._settings.youcam_task_api]
        deadline = self._clock() + self._settings.youcam_task_timeout_s
        while True:
            await self._sleep(self._settings.youcam_poll_interval_s)
            data = self._data(await self._send("GET", f"{YOUCAM_BASE_URL}{path}/{task_id}"), "poll")
            try:
                state = TaskState.model_validate(data)
            except ValidationError:
                raise YouCamError("bad_response", units_possible=True) from None
            if state.task_status == "success":
                self.last_result = data if isinstance(data, dict) else None
                output = (state.results or {}).get("output")
                if not isinstance(output, list):
                    raise YouCamError("unexpected_format")  # e.g. a zip url despite format="json"
                items = []
                for raw in output:
                    try:
                        items.append(OutputItem.model_validate(raw))
                    except ValidationError:
                        log.info("YouCam result: skipped an output item without a type")
                return items
            if state.task_status == "error":
                raise YouCamError(state.error or "task_error")
            if self._clock() >= deadline:
                raise YouCamError("timeout", units_possible=True)

    async def _delete_task(self, task_id: str) -> None:
        """Best effort: a failed delete never fails the analysis (YouCam also expires tasks on its own)."""
        try:
            response = await self._send("POST", f"{YOUCAM_BASE_URL}{DELETE_PATH}", json={"task_id": task_id})
            if not response.is_success:
                log.warning("YouCam task delete returned HTTP %s", response.status_code)
        except (YouCamError, LiveCallRefused):
            log.warning("YouCam task delete could not be sent")

    async def analyse_skin(self, image: bytes, content_type: str, actions: Sequence[str]) -> list[OutputItem]:
        """Run one skin analysis end to end and return the raw output items. The task is deleted afterwards."""
        await self._ensure_credit_floor()
        file_id = await self._register_and_upload(image, content_type)
        task_id = await self._create_task(file_id, actions)
        finished = False
        try:
            items = await self._poll(task_id)
            finished = True
            return items
        except YouCamError as exc:
            finished = exc.code != "timeout"  # a timed-out task may still be running: leave it to expire
            raise
        finally:
            if finished:
                await self._delete_task(task_id)
