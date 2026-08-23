"""Lightweight in-process rate limiting (API_SPEC: rate limit).

Fixed-window per-client-IP counter. Suitable for a single-instance MVP; for
multi-instance deployments move the counter to Redis. Disabled when
RATE_LIMIT_PER_MIN <= 0. /health is always exempt.
"""

from __future__ import annotations

import os
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_min: int | None = None) -> None:
        super().__init__(app)
        env = os.environ.get("RATE_LIMIT_PER_MIN")
        self.limit = int(env) if env is not None else (limit_per_min if limit_per_min is not None else 120)
        self._buckets: dict[str, tuple[int, int]] = {}  # ip -> (window_start, count)

    def _client_ip(self, request: Request) -> str:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if self.limit <= 0 or request.url.path in ("/health", "/"):
            return await call_next(request)

        ip = self._client_ip(request)
        window = int(time.time()) // 60
        start, count = self._buckets.get(ip, (window, 0))
        if start != window:
            start, count = window, 0
        count += 1
        self._buckets[ip] = (start, count)

        if count > self.limit:
            return JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
