from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.snapshot import SnapshotStatus


class SnapshotCreate(BaseModel):
    name: str = Field(min_length=5, max_length=200)
    description: Optional[str] = None
    source_table: str = Field(min_length=1, max_length=100)
    source_query: Optional[str] = None
    file_format: str = Field(default="json", pattern="^(json|csv)$")
    is_public: str = Field(default="N", pattern="^(Y|N)$")
    allowed_roles: Optional[str] = None  # Comma-separated, e.g. "admin,supervisor"


class SnapshotOut(BaseModel):
    id: int
    snapshot_code: str
    name: str
    description: Optional[str] = None
    source_table: str
    record_count: int
    file_size_bytes: int
    file_format: str
    status: SnapshotStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_public: str
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
