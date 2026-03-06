from app.db.database import Base
from app.models.permission import Permission
from app.models.role import Role, role_has_permissions
from app.models.user import User, model_has_roles
from app.models.snapshot import DataSnapshot, SnapshotStatus

# This file imports all models so Alembic or create_all() can discover them.
__all__ = [
    "Base",
    "Permission",
    "Role",
    "User",
    "role_has_permissions",
    "model_has_roles",
    "DataSnapshot",
    "SnapshotStatus",
]
