"""
app/middlewares/error_tracking.py
Middleware untuk catch dan log unhandled exceptions (Chapter 10).
"""
import traceback
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def error_tracking_middleware(request: Request, call_next):
    """
    Catch semua exception yang tidak tertangani oleh endpoint handler,
    log dengan full traceback, lalu kembalikan response 500 yang rapi.
    """
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "event": "unhandled_exception",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                },
            },
        )
