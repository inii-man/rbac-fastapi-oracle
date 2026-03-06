"""
app/api/endpoints/monitoring.py
Monitoring stats endpoint — hanya untuk admin (Chapter 10).
"""
import logging
from datetime import datetime, timedelta, timezone

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_permission
from app.db.database import get_db
from app.models.user import User
from app.models.snapshot import DataSnapshot, SnapshotStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/stats",
    summary="Monitoring Stats (Admin Only)",
    dependencies=[Depends(require_permission("view_monitoring"))],
)
def get_monitoring_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dashboard statistik operasional:
    - Snapshot summary (total, completed, pending, failed)
    - System resources (CPU, memory, disk) via psutil
    Hanya dapat diakses oleh user dengan permission 'view_monitoring'.
    """
    # --- Snapshot stats ---
    total_snapshots = db.query(DataSnapshot).count()
    completed_snapshots = (
        db.query(DataSnapshot)
        .filter(DataSnapshot.status == SnapshotStatus.COMPLETED)
        .count()
    )
    pending_snapshots = (
        db.query(DataSnapshot)
        .filter(DataSnapshot.status == SnapshotStatus.PENDING)
        .count()
    )
    failed_snapshots = (
        db.query(DataSnapshot)
        .filter(DataSnapshot.status == SnapshotStatus.FAILED)
        .count()
    )

    # --- System resources ---
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "success": True,
        "data": {
            "snapshots": {
                "total": total_snapshots,
                "completed": completed_snapshots,
                "pending": pending_snapshots,
                "failed": failed_snapshots,
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used // (1024 * 1024),
                "memory_available_mb": memory.available // (1024 * 1024),
                "memory_total_mb": memory.total // (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024 ** 3), 2),
                "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
