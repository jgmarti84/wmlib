"""Repository pattern for data access."""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.radar import Radar
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
    
    def get_by_id(self, radar_id: UUID) -> Optional[Radar]:
        """Get radar by UUID.
        
        Args:
            radar_id: Radar UUID
            
        Returns:
            Radar instance or None
        """
        return self.session.query(Radar).filter(Radar.id == radar_id).first()
    
    def get_by_radar_id(self, radar_id: str) -> Optional[Radar]:
        """Get radar by radar_id string.
        
        Args:
            radar_id: Radar identifier string
            
        Returns:
            Radar instance or None
        """
        return self.session.query(Radar).filter(Radar.radar_id == radar_id).first()
    
    def get_all_enabled(self) -> List[Radar]:
        """Get all enabled radars.
        
        Returns:
            List of enabled radars
        """
        return self.session.query(Radar).filter(Radar.enabled == True).all()
    
    def create(self, radar: Radar) -> Radar:
        """Create new radar.
        
        Args:
            radar: Radar instance to create
            
        Returns:
            Created radar with ID
        """
        self.session.add(radar)
        self.session.flush()
        logger.info("radar_created", radar_id=radar.radar_id)
        return radar
    
    def update(self, radar: Radar) -> Radar:
        """Update existing radar.
        
        Args:
            radar: Radar instance to update
            
        Returns:
            Updated radar
        """
        radar.updated_at = datetime.utcnow()
        self.session.flush()
        logger.info("radar_updated", radar_id=radar.radar_id)
        return radar


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
    
    def get_pending_for_radar(self, radar_id: UUID, limit: int = 10) -> List[BUFRFile]:
        """Get pending files for a specific radar.
        
        Args:
            radar_id: Radar UUID
            limit: Maximum number of files to return
            
        Returns:
            List of pending BUFR files
        """
        return self.session.query(BUFRFile).filter(
            BUFRFile.radar_id == radar_id,
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
