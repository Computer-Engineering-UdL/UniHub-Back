import asyncio
import ipaddress
import time
from typing import Optional
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import logger, request_id_var
from .rate_limiter import RateLimiter, RateLimitStrategy
from .security import get_payload


def get_client_ip(request: Request) -> str:
    """Extract the real client IP from proxy headers or fallback to direct connection."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            pass

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        try:
            ipaddress.ip_address(real_ip)
            return real_ip
        except ValueError:
            pass

    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        try:
            ipaddress.ip_address(cf_connecting_ip)
            return cf_connecting_ip
        except ValueError:
            pass

    if request.client:
        try:
            ipaddress.ip_address(request.client.host)
            return request.client.host
        except ValueError:
            pass

    return "127.0.0.1"


class AutoLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request_id_var.set(request_id)
        client_ip = get_client_ip(request)

        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_ip,
            },
        )

        start_time = time.time()

        try:
            result = call_next(request)
            if asyncio.iscoroutine(result):
                response = await result
            else:
                response = result
            duration = time.time() - start_time

            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} - ERROR",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "request_id": request_id_var.get()},
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware
    Adds rate limit headers to all responses
    """

    def __init__(
        self, app, max_requests: int = 100, window_seconds: int = 60, exclude_paths: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/health"]

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            result = call_next(request)
            if asyncio.iscoroutine(result):
                return await result
            return result

        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = get_payload(token)
            user_id = payload.get("sub")

        if user_id:
            key = f"global:{user_id}"
        else:
            key = f"global:{request.client.host}"

        is_allowed, remaining, retry_after = await RateLimiter.check_rate_limit(
            key=key,
            max_requests=self.max_requests,
            window_seconds=self.window_seconds,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
        )

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Global rate limit exceeded", "retry_after": retry_after},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

        result = call_next(request)
        if asyncio.iscoroutine(result):
            response = await result
        else:
            response = result

        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)

        return response


class EndpointRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-endpoint rate limiting middleware
    Configure different limits for different endpoints
    """

    def __init__(self, app, endpoint_limits: dict[str, tuple[int, int]]):
        """
        Args:
            app: FastAPI application
            endpoint_limits: Dict of endpoint patterns to (max_requests, window_seconds)
        """
        super().__init__(app)
        self.endpoint_limits = endpoint_limits

    async def dispatch(self, request: Request, call_next):
        max_requests = None
        window_seconds = None

        for pattern, (limit, window) in self.endpoint_limits.items():
            if request.url.path.startswith(pattern):
                max_requests = limit
                window_seconds = window
                break

        if max_requests is None:
            result = call_next(request)
            if asyncio.iscoroutine(result):
                return await result
            return result

        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = get_payload(token)
            user_id = payload.get("sub")

        endpoint_key = request.url.path.replace("/", "_")
        if user_id:
            key = f"endpoint:{endpoint_key}:{user_id}"
        else:
            key = f"endpoint:{endpoint_key}:{request.client.host}"

        is_allowed, remaining, retry_after = await RateLimiter.check_rate_limit(
            key=key, max_requests=max_requests, window_seconds=window_seconds, strategy=RateLimitStrategy.SLIDING_WINDOW
        )

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded for {request.url.path}", "retry_after": retry_after},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        result = call_next(request)
        if asyncio.iscoroutine(result):
            response = await result
        else:
            response = result

        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
