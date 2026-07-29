"""Security hardening middleware — lightweight rate limiting + security headers.

Rate limiting is an in-memory sliding window keyed by (client IP, sensitive path).
It protects credential endpoints against brute force / abuse (STD-005). For multi-pod
horizontal scale this should move to a shared store (Redis); single-pod is sufficient
for the current deployment. Toggle via RATE_LIMIT_ENABLED (default on)."""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# sensitive path -> (max_requests, window_seconds)
_RULES: dict[str, tuple[int, int]] = {
    "/api/auth/login": (100, 60),
    "/api/auth/register": (100, 60),
    "/api/auth/forgot-password": (5, 300),
    "/api/auth/reset-password": (5, 300),
}

_hits: dict[str, deque] = defaultdict(deque)


def _enabled() -> bool:
    return os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"


def _client_ip(request: Request) -> str:
    # Behind the k8s ingress the socket peer is the proxy; trust X-Forwarded-For's
    # first hop for the real client so limits are per-user, not per-proxy.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if _enabled() and request.method == "POST":
            rule = _RULES.get(request.url.path)
            if rule:
                limit, window = rule
                key = f"{_client_ip(request)}:{request.url.path}"
                now = time.time()
                dq = _hits[key]
                while dq and now - dq[0] > window:
                    dq.popleft()
                if len(dq) >= limit:
                    return JSONResponse(
                        status_code=429,
                        content={"error_code": "RATE_LIMITED",
                                 "detail": "Too many requests. Please slow down and try again."})
                dq.append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("X-XSS-Protection", "1; mode=block")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return resp
