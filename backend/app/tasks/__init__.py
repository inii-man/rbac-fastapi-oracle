"""
app/tasks/snapshot_cleanup.py
Scheduled task untuk cleanup snapshot yang sudah expired.
Dapat dijalankan via cron, APScheduler, atau Celery Beat.
"""
import os
import logging
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.snapshot import DataSnapshot, SnapshotStatus

logger = logging.getLogger(__name__)


def cleanup_expired_snapshots():
    """
    Cari semua snapshot yang sudah melewati expires_at,
    hapus file-nya, lalu ubah status ke EXPIRED.

    Jalankan via scheduler, contoh:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(cleanup_expired_snapshots, trigger="cron", hour=2, minute=0)
        scheduler.start()
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        expired = (
            db.query(DataSnapshot)
            .filter(
                DataSnapshot.status == SnapshotStatus.COMPLETED,
                DataSnapshot.expires_at <= now,
            )
            .all()
        )

        for snapshot in expired:
            # Hapus file dari storage
            if snapshot.file_path and os.path.exists(snapshot.file_path):
                try:
                    os.remove(snapshot.file_path)
                    logger.info(f"Deleted snapshot file: {snapshot.file_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete file {snapshot.file_path}: {e}")

            # Update status ke EXPIRED
            snapshot.status = SnapshotStatus.EXPIRED

        db.commit()
        logger.info(f"Snapshot cleanup: {len(expired)} snapshot(s) expired")

    except Exception as e:
        logger.error(f"Snapshot cleanup failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
