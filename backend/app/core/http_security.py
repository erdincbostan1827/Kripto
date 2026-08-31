from __future__ import annotations

import re
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_CORRELATION_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, production: bool = False):
        super().__init__(app)
        self.production = production

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("X-Correlation-ID", "")
        correlation_id = incoming if _CORRELATION_RE.fullmatch(incoming) else uuid.uuid4().hex
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        if request.url.path.startswith("/api/v1/auth"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        if self.production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
