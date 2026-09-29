from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear contextvars to avoid leakage between requests
        clear_contextvars()

        # Extract x-request-id from headers or generate a new one
        correlation_id = request.headers.get("x-request-id")

        if not correlation_id:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        # Bind correlation ID to structlog contextvars
        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()

        try:
            response = await call_next(request)

            # Add correlation ID and processing time to response headers
            response.headers["x-request-id"] = correlation_id

            response_time_ms = (time.perf_counter() - start) * 1000
            response.headers["x-response-time-ms"] = f"{response_time_ms:.2f}"

            return response

        finally:
            # Prevent context leaking to another request
            clear_contextvars()
