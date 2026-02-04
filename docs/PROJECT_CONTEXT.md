## Project Context

You are helping build a production-ready meteorological data visualization platform that processes and displays real-time radar data. The system ingests BUFR files from multiple radar stations via FTP, processes them into Cloud Optimized GeoTIFFs (COGs), and serves them through a web interface with animated radar imagery.

Reference implementation: https://webmet.ohmc.ar/

## Development Approach

### Incremental Development Philosophy
- Build ONE feature at a time
- Each feature must be fully tested before moving to the next
- Start simple, add complexity incrementally
- Wait for user feedback between major components
- Prioritize working code over perfect code

### Current Phase
We are in **MVP Phase 1**: Single radar data ingestion with basic state management.

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Package Manager**: Poetry
- **Framework**: FastAPI (for future API components)
- **Database ORM**: SQLAlchemy 2.0+
- **Async**: asyncio for I/O operations
- **Task Queue**: Celery + Redis (future phases)
- **Testing**: pytest, pytest-asyncio, pytest-cov

### Database
- **Primary**: PostgreSQL 15+ with PostGIS extension
- **Migrations**: Alembic
- **Connection Pooling**: SQLAlchemy pool

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Configuration**: Pydantic Settings with .env support
- **Logging**: structlog for structured logging
- **Monitoring**: Prometheus metrics (future)

### Frontend (Future Phases)
- **Framework**: React or Vue.js with TypeScript
- **Mapping**: Leaflet.js
- **State Management**: React Query or Pinia
- **Build Tool**: Vite

### Geospatial Tools
- **BUFR Decoding**: eccodes-python
- **Raster Processing**: GDAL/rasterio
- **COG Generation**: rio-cogeo
- **Format**: Cloud Optimized GeoTIFF

## Code Style & Standards

### Python Guidelines
```python
# Type hints are MANDATORY
def process_file(file_path: str, radar_id: UUID) -> ProcessingResult:
    """Process a BUFR file and return results.
    
    Args:
        file_path: Absolute path to the BUFR file
        radar_id: UUID of the radar station
        
    Returns:
        ProcessingResult containing status and metadata
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ProcessingError: If BUFR decoding fails
    """
    pass

# Use dataclasses or Pydantic models for data structures
from pydantic import BaseModel, Field

class RadarConfig(BaseModel):
    id: str = Field(..., description="Unique radar identifier")
    name: str
    strategies: List[StrategyConfig]
    
# Use enums for status fields
from enum import Enum

class FileStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Error handling with specific exceptions
class RadarPlatformError(Exception):
    """Base exception for radar platform"""
    pass

class FTPConnectionError(RadarPlatformError):
    """Raised when FTP connection fails"""
    pass

# Logging with structured context
import structlog

logger = structlog.get_logger()

logger.info(
    "file_downloaded",
    file_path=file_path,
    radar_id=str(radar_id),
    size_bytes=file_size,
    duration_seconds=duration
)