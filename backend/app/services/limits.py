"""Daily live-analysis caps: per visitor IP and for the whole server. In memory, single process (one worker).

Counts reset at midnight West Africa Time. A slot is reserved when a photo is accepted and released again if
the analysis fails in a way YouCam does not bill (units are only charged for successful tasks).
The unit balance floor is enforced by the YouCam client itself, right before any upload.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta, timezone

from app.errors import AppError

WAT = timezone(timedelta(hours=1))


def _today() -> date:
    return datetime.now(UTC).astimezone(WAT).date()


class DailyLimiter:
    def __init__(self, today: Callable[[], date] = _today) -> None:
        self._today = today
        self._day: date | None = None
        self._per_ip: dict[str, int] = {}
        self._total = 0

    def _roll(self) -> None:
        day = self._today()
        if day != self._day:
            self._day, self._per_ip, self._total = day, {}, 0

    def reserve(self, ip: str, *, per_ip_max: int, global_max: int) -> None:
        self._roll()
        if self._total >= global_max:
            raise AppError(
                "daily_limit_reached",
                "Today's live analyses are all used up. You can choose a sample profile instead.",
                status=429,
            )
        if self._per_ip.get(ip, 0) >= per_ip_max:
            raise AppError(
                "daily_limit_reached",
                "You've reached today's live analyses on this connection. You can choose a sample profile instead.",
                status=429,
            )
        self._per_ip[ip] = self._per_ip.get(ip, 0) + 1
        self._total += 1

    def release(self, ip: str) -> None:
        self._roll()
        if self._per_ip.get(ip, 0) > 0:
            self._per_ip[ip] -= 1
            self._total = max(0, self._total - 1)
