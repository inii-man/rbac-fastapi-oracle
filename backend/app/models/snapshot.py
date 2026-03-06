from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, Sequence, CheckConstraint
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class SnapshotStatus(str, enum.Enum):
    PENDING = "PENDING"       # Sedang dibuat
    COMPLETED = "COMPLETED"   # Berhasil dibuat
    FAILED = "FAILED"         # Gagal dibuat
    EXPIRED = "EXPIRED"       # Sudah kadaluarsa


class DataSnapshot(Base):
    __tablename__ = "data_snapshots"

    # Oracle: gunakan Sequence eksplisit untuk auto-increment
    # JANGAN pakai index=True pada PK — Oracle sudah otomatis buat indeks untuk PK
    id = Column(Integer, Sequence("data_snapshots_id_seq"), primary_key=True)

    # unique=True sudah membuat indeks di Oracle, tidak perlu index=True
    snapshot_code = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    source_table = Column(String(100), nullable=False)
    source_query = Column(Text)
    record_count = Column(BigInteger, default=0)
    file_size_bytes = Column(BigInteger, default=0)
    file_path = Column(String(500))
    file_format = Column(String(20), default="json")

    # Oracle: simpan status sebagai VARCHAR dengan CheckConstraint
    status = Column(
        String(20),
        nullable=False,
        default=SnapshotStatus.PENDING.value,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_by = Column(String(100))
    created_by_user_id = Column(Integer)
    is_public = Column(String(10), default="N")
    allowed_roles = Column(String(200))

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','COMPLETED','FAILED','EXPIRED')",
            name="chk_snapshot_status",
        ),
    )
