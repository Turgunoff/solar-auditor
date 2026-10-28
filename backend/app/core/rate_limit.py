from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-IP limiter for expensive endpoints.

    Only paths in `limited_prefixes` are counted; everything else passes
    through untouched. State is in-memory (single-process MVP).
    """

    def __init__(self, app, per_minute: int = 60, limited_prefixes=("/api/v1/process", "/api/v1/leads")) -> None:
        super().__init__(app)
        self.per_minute = max(1, per_minute)
        self.limited_prefixes = tuple(limited_prefixes)
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(self.limited_prefixes):
            return await call_next(request)
        now = time.monotonic()
        window = now - 60.0
        ip = request.client.host if request.client else "unknown"
        hits = self._hits[ip]
        while hits and hits[0] <= window:
            hits.popleft()
        if len(hits) >= self.per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded, try again shortly"},
            )
        hits.append(now)
        return await call_next(request)
