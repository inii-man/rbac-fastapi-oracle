"""
app/api/endpoints/health.py
Health check endpoints: liveness, readiness, combined (Chapter 10).
"""
import time
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.database import engine

logger = logging.getLogger(__name__)
router = APIRouter()

_start_time = time.time()


def check_database() -> bool:
    """Coba eksekusi SELECT 1 ke database. Return True jika berhasil."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
        return True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False


@router.get("/live", summary="Liveness Probe")
def liveness_check():
    """
    Liveness probe — selalu return 200 selama proses berjalan.
    Digunakan Kubernetes untuk auto-restart pod yang crash.
    """
    return {"status": "alive", "timestamp": time.time()}


@router.get("/ready", summary="Readiness Probe")
def readiness_check():
    """
    Readiness probe — cek semua dependency kritis (database).
    Return 200 jika siap, 503 jika belum / ada masalah.
    Digunakan load balancer: pod dikeluarkan dari rotasi jika not ready.
    """
    checks = {"database": check_database()}
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": time.time(),
        },
    )


@router.get("", summary="Combined Health Status")
def health_check():
    """
    Combined health check dengan detail uptime dan versi.
    Cocok untuk dashboard monitoring internal.
    """
    db_healthy = check_database()
    uptime_seconds = round(time.time() - _start_time, 1)

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "checks": {
            "database": "pass" if db_healthy else "fail",
        },
        "timestamp": time.time(),
    }
