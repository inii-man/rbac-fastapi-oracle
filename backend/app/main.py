import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator

# --- Setup structured JSON logging (harus di-setup sebelum import lain) ---
from app.logging_config import setup_logging
setup_logging()

from app.middlewares.audit import AuditLogMiddleware
from app.middlewares.request_logging import request_logging_middleware
from app.middlewares.error_tracking import error_tracking_middleware
from app.api.routers import api_router
from app.db.database import engine, Base
from app.core.config import settings
import app.models  # Import semua models agar terdaftar di Base.metadata

# Pastikan direktori penyimpanan snapshot tersedia
os.makedirs("./data/snapshots", exist_ok=True)

# Create tables if they don't exist (In production, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Fullstack RBAC API - Pelatihan 5 Hari",
    version="1.0.0",
)

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Prometheus Metrics: harus di-instrument SEBELUM middleware lain ---
Instrumentator().instrument(app).expose(app)

# --- Middleware (urutan: luar ke dalam, jadi yang pertama di-add = paling luar) ---
# Error tracking paling luar supaya catch semua exception
app.middleware("http")(error_tracking_middleware)

# Request logging
app.middleware("http")(request_logging_middleware)

# Audit log (POST/PUT/DELETE/PATCH)
app.add_middleware(AuditLogMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to the Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(api_router, prefix="/api")
