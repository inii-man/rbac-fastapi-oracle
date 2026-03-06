"""
app/api/endpoints/snapshots.py
Snapshot Data endpoints - Chapter 9 (Day 5)
"""
import os
import json
import csv
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from app.api.dependencies import get_current_user
from app.db.database import get_db, SessionLocal
from app.models.snapshot import DataSnapshot, SnapshotStatus
from app.models.user import User
from app.schemas.snapshot import SnapshotCreate, SnapshotOut

logger = logging.getLogger(__name__)

router = APIRouter()

SNAPSHOT_STORAGE_PATH = "./data/snapshots"


def _now_naive() -> datetime:
    """Return current UTC time as naive datetime.
    Oracle menyimpan datetime tanpa timezone info (offset-naive),
    sehingga perbandingan harus menggunakan naive datetime.
    """
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Helper: Access Control
# ---------------------------------------------------------------------------

def can_access_snapshot(snapshot: DataSnapshot, user: User) -> bool:
    """Periksa apakah user boleh mengakses snapshot ini."""
    # Admin akses semua
    for role in user.roles:
        if role.name == "admin":
            return True
    # Pemilik snapshot
    if snapshot.created_by_user_id == user.id:
        return True
    # Snapshot publik
    if snapshot.is_public == "Y":
        return True
    # Role-based access
    if snapshot.allowed_roles:
        user_roles = {r.name for r in user.roles}
        allowed = {r.strip() for r in snapshot.allowed_roles.split(",")}
        if user_roles & allowed:
            return True
    return False


# ---------------------------------------------------------------------------
# Background Task: Generate Snapshot Content
# ---------------------------------------------------------------------------

def generate_snapshot_content(
    snapshot_id: int,
    source_table: str,
    source_query: Optional[str],
    file_format: str,
):
    """
    Background task untuk generate snapshot content.
    Berjalan asynchronous setelah API response dikembalikan.
    Menggunakan SessionLocal() langsung (bukan dependency injection).
    """
    db = SessionLocal()
    snapshot = None
    try:
        snapshot = db.query(DataSnapshot).filter(DataSnapshot.id == snapshot_id).first()
        if not snapshot:
            logger.error(f"Snapshot {snapshot_id} not found in background task")
            return

        # Query source data
        query_str = source_query if source_query else f"SELECT * FROM {source_table}"
        result = db.execute(text(query_str))
        rows = result.fetchall()
        columns = list(result.keys())
        data = [dict(zip(columns, row)) for row in rows]

        # Pastikan direktori penyimpanan ada
        os.makedirs(SNAPSHOT_STORAGE_PATH, exist_ok=True)

        # Generate file path
        file_name = f"{snapshot.snapshot_code}.{file_format}"
        file_path = os.path.join(SNAPSHOT_STORAGE_PATH, file_name)

        # Tulis data ke file berdasarkan format
        if file_format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        elif file_format == "csv":
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    # Tulis header saja jika data kosong
                    f.write(",".join(columns) + "\n")

        # Update metadata ke COMPLETED
        snapshot.record_count = len(data)
        snapshot.file_size_bytes = os.path.getsize(file_path)
        snapshot.file_path = file_path
        snapshot.status = SnapshotStatus.COMPLETED.value
        snapshot.completed_at = _now_naive()
        db.commit()
        logger.info(f"Snapshot {snapshot_id} completed: {len(data)} records, {snapshot.file_size_bytes} bytes")

    except Exception as e:
        logger.error(f"Failed to generate snapshot {snapshot_id}: {e}", exc_info=True)
        if snapshot:
            snapshot.status = SnapshotStatus.FAILED.value
            snapshot.description = f"Error: {str(e)[:400]}"
            db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SnapshotOut)
def create_snapshot(
    payload: SnapshotCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Buat snapshot data baru.
    Snapshot dibuat secara asynchronous di background task.
    API langsung return 201 dengan status PENDING.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    snapshot_code = f"SNAP-{payload.source_table.upper()}-{timestamp}"

    snapshot = DataSnapshot(
        snapshot_code=snapshot_code,
        name=payload.name,
        description=payload.description,
        source_table=payload.source_table,
        source_query=payload.source_query,
        file_format=payload.file_format,
        status=SnapshotStatus.PENDING.value,
        expires_at=_now_naive() + timedelta(days=30),
        created_by=current_user.username,
        created_by_user_id=current_user.id,
        is_public=payload.is_public,
        allowed_roles=payload.allowed_roles,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    # Delegasikan generate konten ke background task
    background_tasks.add_task(
        generate_snapshot_content,
        snapshot_id=snapshot.id,
        source_table=payload.source_table,
        source_query=payload.source_query,
        file_format=payload.file_format,
    )

    logger.info(f"Snapshot {snapshot_code} created by {current_user.username}, processing in background")
    return snapshot


@router.get("", response_model=List[SnapshotOut])
def list_snapshots(
    snapshot_status: Optional[str] = None,
    source_table: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Daftar semua snapshot yang dapat diakses oleh user saat ini.
    Admin melihat semua, user lain hanya melihat milik sendiri / publik / sesuai role.
    """
    query = db.query(DataSnapshot)

    if snapshot_status:
        query = query.filter(DataSnapshot.status == snapshot_status)
    if source_table:
        query = query.filter(DataSnapshot.source_table == source_table)

    # Access control: user biasa hanya lihat snapshot yang diizinkan
    is_admin = any(r.name == "admin" for r in current_user.roles)
    if not is_admin:
        user_role_names = [r.name for r in current_user.roles]
        role_conditions = [
            DataSnapshot.allowed_roles.like(f"%{rn}%") for rn in user_role_names
        ]
        query = query.filter(
            or_(
                DataSnapshot.is_public == "Y",
                DataSnapshot.created_by_user_id == current_user.id,
                *role_conditions,
            )
        )

    offset = (page - 1) * page_size
    return (
        query.order_by(DataSnapshot.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


@router.get("/{snapshot_id}", response_model=SnapshotOut)
def get_snapshot(
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ambil metadata snapshot berdasarkan ID."""
    snapshot = db.query(DataSnapshot).filter(DataSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    if not can_access_snapshot(snapshot, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    return snapshot


@router.get("/{snapshot_id}/data")
def get_snapshot_data(
    snapshot_id: int,
    format: str = "json",   # "json" atau "download"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Serve isi data snapshot.
    ?format=json    → return data sebagai JSON response
    ?format=download → return file sebagai binary download
    """
    snapshot = db.query(DataSnapshot).filter(DataSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    if not can_access_snapshot(snapshot, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    if snapshot.status != SnapshotStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Snapshot not ready. Current status: {snapshot.status}",
        )
    if snapshot.expires_at and snapshot.expires_at < _now_naive():
        raise HTTPException(status_code=410, detail="Snapshot has expired")
    if not snapshot.file_path or not os.path.exists(snapshot.file_path):
        raise HTTPException(status_code=500, detail="Snapshot file not found on server")

    if format == "download":
        return FileResponse(
            path=snapshot.file_path,
            filename=os.path.basename(snapshot.file_path),
            media_type="application/octet-stream",
        )
    else:
        with open(snapshot.file_path, "r", encoding="utf-8") as f:
            if snapshot.file_format == "csv":
                reader = csv.DictReader(f)
                data = [dict(row) for row in reader]
            else:
                data = json.load(f)
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "snapshot_code": snapshot.snapshot_code,
                    "record_count": snapshot.record_count,
                    "data": data,
                },
            }
        )


@router.delete("/{snapshot_id}", status_code=status.HTTP_200_OK)
def delete_snapshot(
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hapus snapshot (hanya pemilik atau admin).
    Juga menghapus file dari storage.
    """
    snapshot = db.query(DataSnapshot).filter(DataSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    is_admin = any(r.name == "admin" for r in current_user.roles)
    is_owner = snapshot.created_by_user_id == current_user.id
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Access denied")

    # Hapus file jika ada
    if snapshot.file_path and os.path.exists(snapshot.file_path):
        try:
            os.remove(snapshot.file_path)
        except OSError as e:
            logger.warning(f"Could not delete snapshot file {snapshot.file_path}: {e}")

    db.delete(snapshot)
    db.commit()
    logger.info(f"Snapshot {snapshot_id} deleted by {current_user.username}")
    return {"success": True, "message": f"Snapshot {snapshot_id} deleted"}
