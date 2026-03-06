from fastapi import APIRouter
from app.api.endpoints import auth, users, roles, permissions
from app.api.endpoints import snapshots, health, monitoring

api_router = APIRouter()

# --- Hari 1-4: Core RBAC ---
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])

# --- Hari 5: Snapshot Data (Chapter 9) ---
api_router.include_router(snapshots.router, prefix="/snapshots", tags=["snapshots"])

# --- Hari 5: Monitoring & Operations (Chapter 10) ---
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
