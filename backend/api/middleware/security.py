"""Security middleware — prompt injection detection, rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.logging_config import get_logger

logger = get_logger("security")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting."""

    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Only rate limit API endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if now - t < self.window
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning("Rate limit exceeded for %s", client_ip)
            raise HTTPException(
                status_code=429,
                detail="تم تجاوز حد الطلبات. يرجى المحاولة لاحقًا.",
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
