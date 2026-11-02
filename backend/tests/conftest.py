"""Shared test setup. Tests must NEVER be able to use the real YouCam key or reach the real network.

Two autouse fixtures enforce this for every backend test (security finding H2, PR #1 review):

1. `_isolated_settings`: Settings no longer reads backend/.env (the owner's real key lives there) and every
   YOUCAM_* / live-mode environment variable is removed. Tests always run in mock mode with no key.
2. `_no_outbound_network`: any attempt to leave the machine raises `LiveRequestBlocked`, at two levels:
   httpx's real transports (MockTransport is a separate class and keeps working) and raw sockets / DNS
   (loopback stays allowed, which asyncio and TestClient need).

A test that needs HTTP behaviour must use httpx.MockTransport (see docs/TEST_PLAN.md).
"""

from __future__ import annotations

import socket

import httpx
import pytest

LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0", "testserver", ""}  # noqa: S104


class LiveRequestBlocked(RuntimeError):  # noqa: N818  (reads better in test output than "...Error")
    """Raised when a test tries to touch the real network."""


def _blocked(target: object) -> LiveRequestBlocked:
    return LiveRequestBlocked(
        f"Real network access is blocked in tests (target: {target!r}). "
        "Use httpx.MockTransport and the recorded fixtures instead."
    )


def _host_of(address: object) -> str:
    if isinstance(address, tuple) and address:
        return str(address[0])
    return str(address)


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch):
    from app.config import Settings, get_settings

    # Never load backend/.env during tests.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for name in (
        "YOUCAM_API_KEY",
        "YOUCAM_BASE_URL",
        "LIVE_ANALYSIS_ENABLED",
        "MAX_LIVE_PER_DAY",
        "PER_IP_PER_DAY",
        "CREDIT_FLOOR",
        "FRONTEND_ORIGIN",
        "CURRENCY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("YOUCAM_MODE", "mock")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _no_outbound_network(monkeypatch):
    def no_send(self, *args, **kwargs):
        raise _blocked("httpx transport")

    async def no_async_send(self, *args, **kwargs):
        raise _blocked("httpx async transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", no_send)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", no_async_send)

    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def guarded_connect(self, address):
        if _host_of(address) not in LOOPBACK:
            raise _blocked(address)
        return real_connect(self, address)

    def guarded_connect_ex(self, address):
        if _host_of(address) not in LOOPBACK:
            raise _blocked(address)
        return real_connect_ex(self, address)

    def guarded_getaddrinfo(host, *args, **kwargs):
        if str(host) not in LOOPBACK:
            raise _blocked(host)
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    yield
