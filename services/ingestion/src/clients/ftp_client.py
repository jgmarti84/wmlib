"""FTP client for downloading BUFR files."""
from ftplib import FTP, error_perm, error_temp
from pathlib import Path
from typing import List, Optional, Tuple, Generator, Pattern
from datetime import datetime, timezone
import time
import re
import structlog

from src.config import FTPConfig
from src.utils.exceptions import FTPConnectionError, FTPDownloadError, FTPListError
from src.utils.bufr_utils import validate_bufr_filename

logger = structlog.get_logger()


class FTPFileInfo:
    """Information about a file on FTP server."""
    
    def __init__(self, name: str, size: int, modify_time: datetime, path: str):
        """Initialize file info.
        
        Args:
            name: File name
            size: File size in bytes
            modify_time: Last modification time
            path: Full path on FTP server
        """
        self.name = name
        self.size = size
        self.modify_time = modify_time
        self.path = path


class FTPClient:
    """FTP client with connection management and retry logic.
    
    Handles connection to FTP servers, listing files, and downloading
    with automatic retry and error handling.
    """
    
    def __init__(self, config: FTPConfig):
        """Initialize FTP client.
        
        Args:
            config: FTP configuration
        """
        self.config = config
        self.ftp: Optional[FTP] = None
        self._connected = False
        
    def connect(self) -> bool:
        """Connect to FTP server.
        
        Returns:
            True if connection successful
            
        Raises:
            FTPConnectionError: If connection fails
        """
        try:
            logger.info(
                "ftp_connecting",
                host=self.config.host,
                port=self.config.port,
                username=self.config.username
            )
            
            self.ftp = FTP()
            self.ftp.connect(
                self.config.host,
                self.config.port,
                timeout=self.config.timeout
            )
            self.ftp.login(self.config.username, self.config.password)
            
            if self.config.passive_mode:
                self.ftp.set_pasv(True)
            
            self._connected = True
            
            logger.info("ftp_connected", host=self.config.host)
            return True
            
        except Exception as e:
            logger.error(
                "ftp_connection_failed",
                host=self.config.host,
                error=str(e)
            )
            raise FTPConnectionError(
                f"Failed to connect to FTP server: {str(e)}",
                details={"host": self.config.host, "port": self.config.port}
            )
    
    def disconnect(self):
        """Disconnect from FTP server."""
        if self.ftp and self._connected:
            try:
                self.ftp.quit()
                logger.info("ftp_disconnected")
            except Exception as e:
                logger.warning("ftp_disconnect_error", error=str(e))
            finally:
                self._connected = False
                self.ftp = None
    
    def reconnect(self):
        """Reconnect to FTP server."""
        self.disconnect()
        time.sleep(2)  # Brief delay before reconnecting
        self.connect()
    
    def is_connected(self) -> bool:
        """Check if connected to FTP server.
        
        Returns:
            True if connected
        """
        return self._connected and self.ftp is not None
    
    def list_files(
        self, 
        remote_path: str, 
        pattern: Optional[str] = None
    ) -> List[FTPFileInfo]:
        """List files in remote directory.
        
        Args:
            remote_path: Path on FTP server
            pattern: Optional file pattern to filter (e.g., "*.bufr")
            
        Returns:
            List of file information
            
        Raises:
            FTPListError: If listing fails
        """
        if not self.is_connected():
            raise FTPConnectionError("Not connected to FTP server")
        
        try:
            logger.debug("ftp_listing_files", path=remote_path, pattern=pattern)
            
            files = []
            
            # Change to directory
            try:
                self.ftp.cwd(remote_path)
            except error_perm as e:
                logger.warning("ftp_path_not_found", path=remote_path, error=str(e))
                return []
            
            # List files
            file_list = []
            self.ftp.retrlines('LIST', file_list.append)
            
            for line in file_list:
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    # Basic parsing - adjust based on FTP server format
                    name = parts[8]
                    
                    # Skip directories and special entries
                    if parts[0].startswith('d') or name in ['.', '..']:
                        continue
                    
                    # Apply pattern filter if provided
                    if pattern and not self._match_pattern(name, pattern):
                        continue
                    
                    try:
                        size = int(parts[4])
                    except (ValueError, IndexError):
                        size = 0
                    
                    # For simplicity, use current time - in production, parse modify time
                    modify_time = datetime.utcnow()
                    
                    file_path = f"{remote_path}/{name}" if not remote_path.endswith('/') else f"{remote_path}{name}"
                    
                    files.append(FTPFileInfo(
                        name=name,
                        size=size,
                        modify_time=modify_time,
                        path=file_path
                    ))
            
            logger.info("ftp_files_listed", path=remote_path, count=len(files))
            return files
            
        except Exception as e:
            logger.error("ftp_list_failed", path=remote_path, error=str(e))
            raise FTPListError(
                f"Failed to list files: {str(e)}",
                details={"path": remote_path}
            )
    
    def list_dir(self, remote_path: str) -> List[str]:
        """List directory names in remote path.
        
        Args:
            remote_path: Path on FTP server
            
        Returns:
            List of directory names (not full paths, just names)
            
        Raises:
            FTPListError: If listing fails
        """
        if not self.is_connected():
            raise FTPConnectionError("Not connected to FTP server")
        
        try:
            logger.debug("ftp_listing_directories", path=remote_path)
            
            directories = []
            
            # Use MLSD if available (more reliable), otherwise fall back to NLST
            try:
                for name, facts in self.ftp.mlsd(remote_path):
                    # Skip current and parent directory entries
                    if name in ('.', '..'):
                        continue
                    # Only include directories
                    if facts.get('type') == 'dir':
                        directories.append(name)
            except (error_perm, AttributeError):
                # MLSD not supported, try NLST and filter
                # Get all entries
                all_entries = self.ftp.nlst(remote_path)
                
                # Filter to get only directories by trying to CWD into each
                current_dir = self.ftp.pwd()
                for entry in all_entries:
                    # Extract just the name from full path if needed
                    entry_name = entry.split('/')[-1]
                    if entry_name in ('.', '..'):
                        continue
                    
                    try:
                        # Try to change to this directory to verify it's a directory
                        test_path = f"{remote_path}/{entry_name}" if not remote_path.endswith('/') else f"{remote_path}{entry_name}"
                        self.ftp.cwd(test_path)
                        directories.append(entry_name)
                    except error_perm:
                        # Not a directory, skip
                        pass
                
                # Return to original directory
                try:
                    self.ftp.cwd(current_dir)
                except:
                    pass
            
            logger.debug("ftp_directories_listed", path=remote_path, count=len(directories))
            return directories
            
        except Exception as e:
            logger.error("ftp_list_dir_failed", path=remote_path, error=str(e))
            raise FTPListError(
                f"Failed to list directories: {str(e)}",
                details={"path": remote_path}
            )
    
    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        max_retries: int = 3
    ) -> bool:
        """Download file from FTP server with retry logic.
        
        Args:
            remote_path: Full path to file on FTP server
            local_path: Destination path for downloaded file
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if download successful
            
        Raises:
            FTPDownloadError: If download fails after retries
        """
        if not self.is_connected():
            raise FTPConnectionError("Not connected to FTP server")
        
        retry_count = 0
        last_error = None
        
        # Ensure local directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        while retry_count < max_retries:
            try:
                logger.info(
                    "ftp_download_attempt",
                    remote_path=remote_path,
                    local_path=str(local_path),
                    attempt=retry_count + 1
                )
                
                start_time = time.time()
                
                with open(local_path, 'wb') as f:
                    self.ftp.retrbinary(f'RETR {remote_path}', f.write)
                
                duration = time.time() - start_time
                file_size = local_path.stat().st_size
                
                logger.info(
                    "ftp_download_success",
                    remote_path=remote_path,
                    local_path=str(local_path),
                    size_bytes=file_size,
                    duration_seconds=round(duration, 2)
                )
                
                return True
                
            except (error_perm, error_temp) as e:
                last_error = e
                logger.warning(
                    "ftp_download_retry",
                    remote_path=remote_path,
                    attempt=retry_count + 1,
                    error=str(e)
                )
                retry_count += 1
                
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    time.sleep(wait_time)
                    
                    # Try to reconnect
                    try:
                        self.reconnect()
                    except Exception as reconnect_error:
                        logger.error(
                            "ftp_reconnect_failed",
                            error=str(reconnect_error)
                        )
                        
            except Exception as e:
                last_error = e
                logger.error(
                    "ftp_download_unexpected_error",
                    remote_path=remote_path,
                    error=str(e)
                )
                break
        
        # All retries exhausted
        logger.error(
            "ftp_download_failed",
            remote_path=remote_path,
            total_attempts=retry_count,
            error=str(last_error)
        )
        
        raise FTPDownloadError(
            f"Failed to download file after {retry_count} attempts: {str(last_error)}",
            details={"remote_path": remote_path, "attempts": retry_count}
        )
    
    def traverse_radar(
        self,
        radar_name: str,
        dt_start: Optional[datetime] = None,
        dt_end: Optional[datetime] = None,
        include_start: bool = True,
        include_end: bool = True,
        vol_types: Optional[Pattern] = None,
    ) -> Generator[Tuple[datetime, str, str], None, None]:
        """
        Traverse FTP folders for BUFR files in hierarchical date structure.
        
        Expected FTP structure: /{base_path}/{radar_name}/YYYY/MM/DD/HH/MMSS/
        Files follow pattern: RADAR_VOLCODE_VOLNR_FIELD_TIMESTAMP.BUFR
        
        Args:
            radar_name: Radar identifier (e.g., 'RMA1', 'RMA11')
            dt_start: Start datetime (UTC), defaults to datetime.min if None
            dt_end: End datetime (UTC), defaults to datetime.max if None
            include_start: Include files at dt_start time
            include_end: Include files at dt_end time
            vol_types: Optional compiled regex pattern to filter by volume types
            
        Yields:
            Tuple of (datetime, filename, remote_path)
            
        Example:
            >>> for dt, fname, path in client.traverse_radar('RMA11', dt_start, dt_end):
            >>>     print(f"{dt}: {fname}")
        """
        if not self.is_connected():
            raise FTPConnectionError("Not connected to FTP server")
        
        base_path = f"{self.config.base_path}/{radar_name}"
        
        if dt_start is None:
            dt_start = datetime.min.replace(tzinfo=timezone.utc)
        if dt_end is None:
            dt_end = datetime.max.replace(tzinfo=timezone.utc)
        
        try:
            # Traverse year directories
            years = sorted(self.list_dir(base_path))
            for year in years:
                try:
                    year_int = int(year)
                except ValueError:
                    continue
                    
                if year_int < dt_start.year or year_int > dt_end.year:
                    continue
                    
                year_path = f"{base_path}/{year}"
                
                # Traverse month directories
                months = sorted(self.list_dir(year_path))
                for month in months:
                    try:
                        month_int = int(month)
                    except ValueError:
                        continue
                        
                    if year_int == dt_start.year and month_int < dt_start.month:
                        continue
                    if year_int == dt_end.year and month_int > dt_end.month:
                        continue
                        
                    month_path = f"{year_path}/{month}"
                    
                    # Traverse day directories
                    days = sorted(self.list_dir(month_path))
                    for day in days:
                        try:
                            day_int = int(day)
                        except ValueError:
                            continue
                            
                        if year_int == dt_start.year and month_int == dt_start.month and day_int < dt_start.day:
                            continue
                        if year_int == dt_end.year and month_int == dt_end.month and day_int > dt_end.day:
                            continue
                            
                        day_path = f"{month_path}/{day}"
                        
                        # Traverse hour directories
                        hours = sorted(self.list_dir(day_path))
                        for hour in hours:
                            try:
                                hour_int = int(hour)
                            except ValueError:
                                continue
                                
                            if (year_int == dt_start.year and month_int == dt_start.month and 
                                day_int == dt_start.day and hour_int < dt_start.hour):
                                continue
                            if (year_int == dt_end.year and month_int == dt_end.month and 
                                day_int == dt_end.day and hour_int > dt_end.hour):
                                continue
                                
                            hour_path = f"{day_path}/{hour}"
                            
                            # Traverse minute/second directories (format: MMSS)
                            minutes = sorted(self.list_dir(hour_path))
                            for minute_str in minutes:
                                try:
                                    # Extract minute and second from MMSS format
                                    minute_int = int(minute_str[:2])
                                    second_int = int(minute_str[2:]) if len(minute_str) > 2 else 0
                                except ValueError:
                                    continue
                                    
                                # Build datetime for this directory
                                try:
                                    dt = datetime(
                                        year_int, month_int, day_int,
                                        hour_int, minute_int, second_int,
                                        tzinfo=timezone.utc
                                    )
                                except ValueError:
                                    continue
                                
                                # Apply datetime range filtering with inclusivity
                                if include_start:
                                    if dt < dt_start:
                                        continue
                                else:
                                    if dt <= dt_start:
                                        continue
                                
                                if include_end:
                                    if dt > dt_end:
                                        continue
                                else:
                                    if dt >= dt_end:
                                        continue
                                
                                # List files in this minute directory
                                minute_path = f"{hour_path}/{minute_str}"
                                file_infos = self.list_files(minute_path)
                                
                                for file_info in file_infos:
                                    filename = file_info.name
                                    # Filter by vol_types if provided
                                    if vol_types is not None:
                                        if not vol_types.match(filename):
                                            continue
                                    
                                    # Validate BUFR filename
                                    if not validate_bufr_filename(filename):
                                        continue
                                    
                                    full_remote_path = f"{minute_path}/{filename}"
                                    yield dt, filename, full_remote_path
                                    
        except FTPListError as e:
            logger.error("traverse_failed", radar_name=radar_name, error=str(e))
        except Exception as e:
            logger.error("traverse_unexpected_error", radar_name=radar_name, error=str(e))
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching for file names.
        
        Args:
            filename: File name to check
            pattern: Pattern to match (supports * wildcard)
            
        Returns:
            True if filename matches pattern
        """
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
