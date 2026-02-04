"""Radar configuration model."""
from sqlalchemy import Column, String, DateTime, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy import func

from src.models import Base


class Radar(Base):
    """Radar station configuration and metadata.
    
    Stores configuration for each radar station including location,
    status, and metadata. Strategies are linked via RadarStrategy table.
    """
    
    __tablename__ = "radars"
    
    code = Column(String(16), primary_key=True)
    title = Column(String(64), nullable=False)
    description = Column(String(64), nullable=True)
    center_lat = Column(Numeric(12, 8), nullable=False)
    center_long = Column(Numeric(12, 8), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    bufr_files = relationship("BUFRFile", back_populates="radar", cascade="all, delete-orphan")
    radar_strategies = relationship("RadarStrategy", back_populates="radar", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Radar(code='{self.code}', title='{self.title}', is_active={self.is_active})>"
