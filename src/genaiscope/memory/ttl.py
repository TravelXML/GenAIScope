"""TTL helpers for memory backends."""

from __future__ import annotations

from datetime import datetime, timedelta

from genaiscope.memory.utils import utc_now


def calculate_expiry(
    ttl_seconds: int | None = None, ttl_days: int | None = None
) -> tuple[int | None, datetime | None]:
    """Calculate normalized TTL seconds and expiry timestamp."""

    seconds = ttl_seconds if ttl_seconds is not None else ttl_days * 86400 if ttl_days else None
    if seconds is None:
        return None, None
    if seconds <= 0:
        raise ValueError("TTL must be greater than zero")
    return seconds, utc_now() + timedelta(seconds=seconds)


def is_expired(expires_at: datetime | None) -> bool:
    """Return whether an expiry timestamp has passed."""

    return expires_at is not None and expires_at <= utc_now()
