"""
app/middlewares/request_logging.py
Middleware untuk otomatis log semua HTTP request beserta detail response (Chapter 10).
"""
import time
import logging
from typing import Callable

from fastapi import Request
from jose import jwt, JWTError

logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next: Callable):
    """
    Log setiap request: method, path, status code, durasi, client IP, dan user (jika autentikasi).
    Di-register di main.py via: app.middleware("http")(request_logging_middleware)
    """
    start_time = time.time()
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    # Coba ekstrak user dari JWT token (skip jika tidak ada)
    user_id, username = None, None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.core.config import settings
            token = auth_header.split(" ", 1)[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            username = payload.get("username")
        except (JWTError, Exception):
            pass  # Biarkan endpoint handler yang tangani auth error

    # Proses request
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)

    logger.info(
        f"{method} {path} {response.status_code} [{duration_ms}ms]",
        extra={
            "event": "http_request",
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_id": user_id,
            "username": username,
        },
    )
    return response
