from __future__ import annotations

from collections.abc import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces enterprise zero-trust security headers on all HTTP responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # HSTS - Force TLS in production
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer control
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features (allow mic for interview recording)
        response.headers["Permissions-Policy"] = "microphone=(self), camera=(), geolocation=()"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: http: https:; "
            "frame-ancestors 'none';"
        )

        return response
