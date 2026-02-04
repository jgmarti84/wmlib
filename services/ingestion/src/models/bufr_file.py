"""BUFR file tracking model."""
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import Column, String, DateTime, Integer, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from src.models import Base


class FileStatus(str, Enum):
    """File processing status enum."""
    
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BUFRFile(Base):
    """BUFR file tracking and state management.
    
    Tracks the lifecycle of each BUFR file from discovery
    through download and processing.
    """
    
    __tablename__ = "bufr_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    radar_id = Column(UUID(as_uuid=True), ForeignKey("radars.id"), nullable=False)
    file_path = Column(String(512), nullable=False, unique=True)
    remote_path = Column(String(512), nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    strategy = Column(String(50), nullable=False)
    volume = Column(String(10), nullable=False)
    status = Column(SQLEnum(FileStatus), nullable=False, default=FileStatus.PENDING)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # Relationships
    radar = relationship("Radar", back_populates="bufr_files")
    
    # Indexes
    __table_args__ = (
        Index('idx_bufr_files_radar_datetime', 'radar_id', 'datetime'),
        Index('idx_bufr_files_status', 'status'),
        Index('idx_bufr_files_radar_status', 'radar_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<BUFRFile(file_path='{self.file_path}', status='{self.status.value}')>"
