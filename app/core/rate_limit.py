from collections import defaultdict
from time import time

from fastapi import HTTPException, Request, status

_buckets: dict[str, list[float]] = defaultdict(list)
_MAX_TRACKED_KEYS = 10_000


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting reverse proxy headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First IP in the chain is the original client
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request, *, key_prefix: str, max_calls: int, window_seconds: int) -> None:
    client = _get_client_ip(request)
    key = f"{key_prefix}:{client}"
    now = time()

    # Prune expired entries for this key
    window = [t for t in _buckets[key] if now - t < window_seconds]

    if len(window) >= max_calls:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
        )

    window.append(now)
    _buckets[key] = window

    # Periodic cleanup: if too many keys tracked, remove stale ones
    if len(_buckets) > _MAX_TRACKED_KEYS:
        stale_keys = [
            k for k, timestamps in _buckets.items()
            if not timestamps or (now - max(timestamps)) > 3600
        ]
        for k in stale_keys:
            del _buckets[k]
