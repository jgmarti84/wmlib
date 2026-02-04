"""Radar configuration model."""
from datetime import datetime
from typing import List
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import Base


class Radar(Base):
    """Radar station configuration and metadata.
    
    Stores configuration for each radar station including its
    strategies and volumes for data collection.
    """
    
    __tablename__ = "radars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    radar_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    strategies = Column(JSON, nullable=False)  # Store strategies configuration as JSON
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bufr_files = relationship("BUFRFile", back_populates="radar", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Radar(radar_id='{self.radar_id}', name='{self.name}', enabled={self.enabled})>"
