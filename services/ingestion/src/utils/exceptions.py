"""Custom exceptions for the ingestion service."""
from typing import Optional, Dict, Any


class RadarPlatformError(Exception):
    """Base exception for all radar platform errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize exception with message and optional details.
        
        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(RadarPlatformError):
    """Raised when configuration is invalid."""
    pass


class FTPError(RadarPlatformError):
    """Base class for FTP-related errors."""
    pass


class FTPConnectionError(FTPError):
    """Raised when FTP connection fails."""
    pass


class FTPDownloadError(FTPError):
    """Raised when file download fails."""
    pass


class FTPListError(FTPError):
    """Raised when listing files fails."""
    pass


class ProcessingError(RadarPlatformError):
    """Base class for processing errors."""
    pass


class DatabaseError(RadarPlatformError):
    """Raised when database operations fail."""
    pass
