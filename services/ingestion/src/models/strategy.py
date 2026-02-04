"""Strategy and Volume configuration models."""
from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func

from src.models import Base


class Strategy(Base):
    """Radar scanning strategy configuration.
    
    Stores strategy configurations that can be applied to radars.
    Strategies define the scanning patterns and volumes to collect.
    """
    
    __tablename__ = "strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    volumes = relationship("Volume", back_populates="strategy", cascade="all, delete-orphan")
    radar_strategies = relationship("RadarStrategy", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Strategy(strategy_id='{self.strategy_id}', name='{self.name}')>"


class Volume(Base):
    """Volume configuration for a strategy.
    
    Defines the specific volumes and fields collected for a strategy.
    """
    
    __tablename__ = "volumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    volume_number = Column(String(10), nullable=False)
    fields = Column(String(500), nullable=False)  # Comma-separated field list
    sort_order = Column(Integer, default=0)  # Order for display/processing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    strategy = relationship("Strategy", back_populates="volumes")
    
    def __repr__(self) -> str:
        return f"<Volume(strategy_id='{self.strategy_id}', volume_number='{self.volume_number}')>"


class RadarStrategy(Base):
    """Association between radars and strategies.
    
    Links radars to their active strategies, allowing dynamic
    strategy assignment and multiple strategies per radar.
    """
    
    __tablename__ = "radar_strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    radar_code = Column(String(16), ForeignKey("radars.code"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0)  # For ordering when multiple strategies exist
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    radar = relationship("Radar", back_populates="radar_strategies")
    strategy = relationship("Strategy", back_populates="radar_strategies")
    
    def __repr__(self) -> str:
        return f"<RadarStrategy(radar_code='{self.radar_code}', strategy_id='{self.strategy_id}')>"
