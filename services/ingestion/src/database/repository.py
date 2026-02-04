"""Repository pattern for data access."""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.radar import Radar
from src.models.strategy import Strategy, Volume, RadarStrategy
from src.models.bufr_file import BUFRFile, FileStatus
import structlog

logger = structlog.get_logger()


class RadarRepository:
    """Repository for Radar operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    def get_by_code(self, code: str) -> Optional[Radar]:
        """Get radar by code.
        
        Args:
            code: Radar code (primary key)
            
        Returns:
            Radar instance or None
        """
        return self.session.query(Radar).filter(Radar.code == code).first()
    
    def get_all_active(self) -> List[Radar]:
        """Get all active radars.
        
        Returns:
            List of active radars
        """
        return self.session.query(Radar).filter(Radar.is_active == True).all()
    
    def create(self, radar: Radar) -> Radar:
        """Create new radar.
        
        Args:
            radar: Radar instance to create
            
        Returns:
            Created radar
        """
        self.session.add(radar)
        self.session.flush()
        logger.info("radar_created", radar_code=radar.code)
        return radar
    
    def update(self, radar: Radar) -> Radar:
        """Update existing radar.
        
        Args:
            radar: Radar instance to update
            
        Returns:
            Updated radar
        """
        self.session.flush()
        logger.info("radar_updated", radar_code=radar.code)
        return radar


class StrategyRepository:
    """Repository for Strategy operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    def get_by_id(self, strategy_id: UUID) -> Optional[Strategy]:
        """Get strategy by UUID.
        
        Args:
            strategy_id: Strategy UUID
            
        Returns:
            Strategy instance or None
        """
        return self.session.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    def get_by_strategy_id(self, strategy_id: str) -> Optional[Strategy]:
        """Get strategy by strategy_id string.
        
        Args:
            strategy_id: Strategy identifier string
            
        Returns:
            Strategy instance or None
        """
        return self.session.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
    
    def get_all_active(self) -> List[Strategy]:
        """Get all active strategies.
        
        Returns:
            List of active strategies
        """
        return self.session.query(Strategy).filter(Strategy.is_active == True).all()
    
    def create(self, strategy: Strategy) -> Strategy:
        """Create new strategy.
        
        Args:
            strategy: Strategy instance to create
            
        Returns:
            Created strategy
        """
        self.session.add(strategy)
        self.session.flush()
        logger.info("strategy_created", strategy_id=strategy.strategy_id)
        return strategy
    
    def get_strategies_for_radar(self, radar_code: str) -> List[Strategy]:
        """Get active strategies for a radar.
        
        Args:
            radar_code: Radar code
            
        Returns:
            List of active strategies
        """
        return self.session.query(Strategy).join(
            RadarStrategy
        ).filter(
            RadarStrategy.radar_code == radar_code,
            RadarStrategy.is_active == True,
            Strategy.is_active == True
        ).order_by(RadarStrategy.priority).all()


class BUFRFileRepository:
    """Repository for BUFR file operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    def get_by_id(self, file_id: UUID) -> Optional[BUFRFile]:
        """Get file by UUID.
        
        Args:
            file_id: File UUID
            
        Returns:
            BUFRFile instance or None
        """
        return self.session.query(BUFRFile).filter(BUFRFile.id == file_id).first()
    
    def get_by_path(self, file_path: str) -> Optional[BUFRFile]:
        """Get file by path.
        
        Args:
            file_path: File path
            
        Returns:
            BUFRFile instance or None
        """
        return self.session.query(BUFRFile).filter(BUFRFile.file_path == file_path).first()
    
    def get_by_status(self, status: FileStatus, limit: int = 100) -> List[BUFRFile]:
        """Get files by status.
        
        Args:
            status: File status to filter by
            limit: Maximum number of files to return
            
        Returns:
            List of BUFR files
        """
        return self.session.query(BUFRFile).filter(
            BUFRFile.status == status
        ).limit(limit).all()
    
    def get_pending_for_radar(self, radar_code: str, limit: int = 10) -> List[BUFRFile]:
        """Get pending files for a specific radar.
        
        Args:
            radar_code: Radar code
            limit: Maximum number of files to return
            
        Returns:
            List of pending BUFR files
        """
        return self.session.query(BUFRFile).filter(
            BUFRFile.radar_code == radar_code,
            BUFRFile.status == FileStatus.PENDING
        ).order_by(BUFRFile.datetime).limit(limit).all()
    
    def create(self, bufr_file: BUFRFile) -> BUFRFile:
        """Create new BUFR file record.
        
        Args:
            bufr_file: BUFRFile instance to create
            
        Returns:
            Created file with ID
        """
        self.session.add(bufr_file)
        self.session.flush()
        logger.info("bufr_file_created", file_path=bufr_file.file_path)
        return bufr_file
    
    def update_status(
        self, 
        file_id: UUID, 
        status: FileStatus, 
        error_message: Optional[str] = None
    ) -> Optional[BUFRFile]:
        """Update file status.
        
        Args:
            file_id: File UUID
            status: New status
            error_message: Optional error message
            
        Returns:
            Updated file or None
        """
        bufr_file = self.get_by_id(file_id)
        if bufr_file:
            bufr_file.status = status
            bufr_file.updated_at = datetime.utcnow()
            if error_message:
                bufr_file.error_message = error_message
            self.session.flush()
            logger.info(
                "bufr_file_status_updated",
                file_id=str(file_id),
                status=status.value
            )
        return bufr_file
    
    def increment_retry(self, file_id: UUID) -> Optional[BUFRFile]:
        """Increment retry count for a file.
        
        Args:
            file_id: File UUID
            
        Returns:
            Updated file or None
        """
        bufr_file = self.get_by_id(file_id)
        if bufr_file:
            bufr_file.retry_count += 1
            bufr_file.updated_at = datetime.utcnow()
            self.session.flush()
            logger.info(
                "bufr_file_retry_incremented",
                file_id=str(file_id),
                retry_count=bufr_file.retry_count
            )
        return bufr_file
