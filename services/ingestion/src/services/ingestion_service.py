"""Main ingestion service for FTP monitoring and file download."""
from pathlib import Path
from typing import List, Optional, Pattern
from datetime import datetime, timezone
import time
import structlog

from src.config import Settings
from src.database import DatabaseManager
from src.database.repository import RadarRepository, BUFRFileRepository
from src.clients import FTPClient
from src.models.radar import Radar
from src.models.bufr_file import BUFRFile, FileStatus
from src.utils.exceptions import FTPError, DatabaseError
from src.utils.bufr_utils import (
    extract_bufr_filename_components,
    build_vol_types_regex,
    parse_bufr_timestamp
)

logger = structlog.get_logger()


class IngestionService:
    """Service for monitoring FTP and downloading BUFR files.
    
    Orchestrates the ingestion workflow:
    1. Poll FTP server for new files
    2. Track files in database
    3. Download files with retry logic
    4. Update file status
    """
    
    def __init__(self, settings: Settings, db_manager: DatabaseManager):
        """Initialize ingestion service.
        
        Args:
            settings: Application settings
            db_manager: Database manager
        """
        self.settings = settings
        self.db_manager = db_manager
        self.ftp_client = FTPClient(settings.ftp)
        
    def initialize_radars(self):
        """Initialize radar configurations from settings.
        
        Creates or updates radar records in the database.
        """
        with self.db_manager.get_session() as session:
            radar_repo = RadarRepository(session)
            
            for radar_config in self.settings.radars:
                existing_radar = radar_repo.get_by_radar_id(radar_config.id)
                
                if existing_radar:
                    # Update existing radar
                    existing_radar.name = radar_config.name
                    existing_radar.enabled = radar_config.enabled
                    existing_radar.strategies = [
                        {
                            "strategy_id": s.strategy_id,
                            "volumes": [
                                {"number": v.number, "fields": v.fields}
                                for v in s.volumes
                            ]
                        }
                        for s in radar_config.strategies
                    ]
                    radar_repo.update(existing_radar)
                    logger.info("radar_updated", radar_id=radar_config.id)
                else:
                    # Create new radar
                    radar = Radar(
                        radar_id=radar_config.id,
                        name=radar_config.name,
                        enabled=radar_config.enabled,
                        strategies=[
                            {
                                "strategy_id": s.strategy_id,
                                "volumes": [
                                    {"number": v.number, "fields": v.fields}
                                    for v in s.volumes
                                ]
                            }
                            for s in radar_config.strategies
                        ]
                    )
                    radar_repo.create(radar)
                    logger.info("radar_created", radar_id=radar_config.id)
    
    def scan_ftp_for_files(
        self, 
        radar: Radar,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[tuple]:
        """Scan FTP server for new BUFR files using hierarchical traversal.
        
        Traverses FTP structure: /{base_path}/{radar_id}/YYYY/MM/DD/HH/MMSS/
        Files must match pattern: RADAR_VOLCODE_VOLNR_FIELD_TIMESTAMP.BUFR
        
        Args:
            radar: Radar configuration
            start_date: Start datetime for scanning (UTC), defaults to 1 hour ago
            end_date: End datetime for scanning (UTC), defaults to now
            
        Returns:
            List of tuples: (datetime, filename, remote_path)
        """
        logger.info("scanning_ftp", radar_id=radar.radar_id)
        
        # Set default date range if not provided (last hour)
        if start_date is None:
            start_date = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            start_date = start_date.replace(hour=start_date.hour - 1)
        
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        # Build vol_types regex from radar strategies
        vol_types_dict = {}
        for strategy_config in radar.strategies:
            strategy_id = strategy_config["strategy_id"]
            vol_types_dict[strategy_id] = {}
            
            for volume_config in strategy_config["volumes"]:
                volume_num = volume_config["number"]
                fields = volume_config["fields"]
                vol_types_dict[strategy_id][volume_num] = fields
        
        vol_types_regex = build_vol_types_regex(vol_types_dict)
        
        logger.debug(
            "ftp_scan_parameters",
            radar_id=radar.radar_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            vol_types=vol_types_dict
        )
        
        remote_files = []
        
        try:
            # Use traverse_radar method for hierarchical scanning
            for dt, filename, remote_path in self.ftp_client.traverse_radar(
                radar_name=radar.radar_id,
                dt_start=start_date,
                dt_end=end_date,
                include_start=False,  # Don't re-download files at start boundary
                vol_types=vol_types_regex
            ):
                remote_files.append((dt, filename, remote_path))
                
                logger.debug(
                    "ftp_file_found",
                    radar_id=radar.radar_id,
                    filename=filename,
                    datetime=dt.isoformat()
                )
            
            logger.info(
                "ftp_scan_complete",
                radar_id=radar.radar_id,
                total_files=len(remote_files),
                date_range=f"{start_date.isoformat()} to {end_date.isoformat()}"
            )
            
        except Exception as e:
            logger.error(
                "ftp_scan_error",
                radar_id=radar.radar_id,
                error=str(e)
            )
        
        return remote_files
    
    def track_new_files(self, radar: Radar, remote_files: List[tuple]):
        """Track new files in database.
        
        Args:
            radar: Radar instance
            remote_files: List of tuples (datetime, filename, remote_path)
        """
        with self.db_manager.get_session() as session:
            file_repo = BUFRFileRepository(session)
            
            new_count = 0
            
            for dt, filename, remote_path in remote_files:
                # Generate local path based on radar and filename
                local_path = self.settings.storage.bufr_path / radar.radar_id / filename
                
                # Check if file already tracked
                existing = file_repo.get_by_path(str(local_path))
                if existing:
                    continue
                
                # Extract components from filename
                components = extract_bufr_filename_components(filename)
                strategy = components.get("strategy", "unknown")
                volume = components.get("vol_nr", "unknown")
                
                # Create new file record
                bufr_file = BUFRFile(
                    radar_id=radar.id,
                    file_path=str(local_path),
                    remote_path=remote_path,
                    datetime=dt,
                    strategy=strategy,
                    volume=volume,
                    status=FileStatus.PENDING
                )
                
                file_repo.create(bufr_file)
                new_count += 1
            
            logger.info(
                "new_files_tracked",
                radar_id=radar.radar_id,
                new_files=new_count
            )
    
    def download_pending_files(self, radar: Radar, max_files: int = 10):
        """Download pending files for a radar.
        
        Args:
            radar: Radar instance
            max_files: Maximum number of files to download
        """
        with self.db_manager.get_session() as session:
            file_repo = BUFRFileRepository(session)
            
            pending_files = file_repo.get_pending_for_radar(radar.id, limit=max_files)
            
            logger.info(
                "downloading_files",
                radar_id=radar.radar_id,
                pending_count=len(pending_files)
            )
            
            for bufr_file in pending_files:
                # Update status to downloading
                file_repo.update_status(bufr_file.id, FileStatus.DOWNLOADING)
                session.commit()
                
                try:
                    # Download file
                    local_path = Path(bufr_file.file_path)
                    success = self.ftp_client.download_file(
                        bufr_file.remote_path,
                        local_path,
                        max_retries=self.settings.app.retry_max_attempts
                    )
                    
                    if success:
                        # Update status to downloaded
                        file_repo.update_status(bufr_file.id, FileStatus.DOWNLOADED)
                        bufr_file.file_size = local_path.stat().st_size
                        session.commit()
                        
                        logger.info(
                            "file_downloaded",
                            file_path=bufr_file.file_path,
                            size_bytes=bufr_file.file_size
                        )
                    
                except Exception as e:
                    # Update status to failed
                    file_repo.update_status(
                        bufr_file.id,
                        FileStatus.FAILED,
                        error_message=str(e)
                    )
                    file_repo.increment_retry(bufr_file.id)
                    session.commit()
                    
                    logger.error(
                        "file_download_failed",
                        file_path=bufr_file.file_path,
                        error=str(e)
                    )
    
    def process_radar(self, radar: Radar):
        """Process a single radar: scan FTP and download files.
        
        Args:
            radar: Radar instance
        """
        logger.info("processing_radar", radar_id=radar.radar_id)
        
        try:
            # Scan FTP for files
            remote_files = self.scan_ftp_for_files(radar)
            
            # Track new files
            if remote_files:
                self.track_new_files(radar, remote_files)
            
            # Download pending files
            self.download_pending_files(radar)
            
            logger.info("radar_processing_complete", radar_id=radar.radar_id)
            
        except Exception as e:
            logger.error(
                "radar_processing_failed",
                radar_id=radar.radar_id,
                error=str(e)
            )
    
    def run_once(self):
        """Run one iteration of the ingestion process."""
        logger.info("ingestion_iteration_start")
        
        try:
            # Connect to FTP
            self.ftp_client.connect()
            
            # Get all enabled radars
            with self.db_manager.get_session() as session:
                radar_repo = RadarRepository(session)
                radars = radar_repo.get_all_enabled()
                
                logger.info("enabled_radars_found", count=len(radars))
                
                for radar in radars:
                    self.process_radar(radar)
            
        except Exception as e:
            logger.error("ingestion_iteration_failed", error=str(e))
            
        finally:
            # Disconnect from FTP
            self.ftp_client.disconnect()
        
        logger.info("ingestion_iteration_complete")
    
    def run_continuous(self):
        """Run continuous ingestion with polling."""
        logger.info(
            "ingestion_service_started",
            polling_interval=self.settings.app.polling_interval
        )
        
        while True:
            try:
                self.run_once()
                
                # Sleep until next iteration
                logger.info(
                    "waiting_for_next_iteration",
                    seconds=self.settings.app.polling_interval
                )
                time.sleep(self.settings.app.polling_interval)
                
            except KeyboardInterrupt:
                logger.info("ingestion_service_stopped")
                break
            except Exception as e:
                logger.error(
                    "ingestion_service_error",
                    error=str(e)
                )
                # Wait a bit before retrying
                time.sleep(30)
