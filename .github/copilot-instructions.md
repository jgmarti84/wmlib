# GitHub Copilot Custom Instructions - Meteorological Data Visualization Platform

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
```

### Code Organization
```
services/
├── ingestion/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point
│   │   ├── config.py            # Configuration management
│   │   ├── models/              # Database models
│   │   │   ├── __init__.py
│   │   │   ├── radar.py
│   │   │   └── bufr_file.py
│   │   ├── clients/             # External service clients
│   │   │   ├── __init__.py
│   │   │   └── ftp_client.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   └── ingestion_service.py
│   │   ├── database/            # Database utilities
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   └── repository.py
│   │   └── utils/               # Helper functions
│   │       ├── __init__.py
│   │       └── datetime_utils.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest fixtures
│   │   ├── unit/                # Unit tests
│   │   │   └── test_ftp_client.py
│   │   └── integration/         # Integration tests
│   │       └── test_ingestion_flow.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
```

### Documentation Standards
#### File Headers
```python
"""Module for FTP client operations.

This module provides a client for connecting to FTP servers,
listing files, and downloading BUFR data files with retry logic
and error handling.

Example:
    >>> client = FTPClient(config)
    >>> client.connect()
    >>> files = client.list_files("/radar_data", datetime.now())
"""
```
#### Function Documentation (Google Style)
```python
def download_file(
    self,
    remote_path: str,
    local_path: str,
    max_retries: int = 3
) -> DownloadResult:
    """Download a file from FTP server with retry logic.
    
    Downloads the specified file and validates the transfer by
    comparing file sizes. Automatically retries on failure.
    
    Args:
        remote_path: Full path to file on FTP server
        local_path: Destination path for downloaded file
        max_retries: Maximum number of retry attempts
        
    Returns:
        DownloadResult with status, file size, and duration
        
    Raises:
        FTPConnectionError: If connection is lost
        FileNotFoundError: If remote file doesn't exist
        DiskSpaceError: If insufficient local storage
        
    Example:
        >>> result = client.download_file(
        ...     "/data/2024/01/15/file.bufr",
        ...     "/local/data/file.bufr"
        ... )
        >>> print(result.status)
        'success'
    """
```

### Readme Structure
```
# Service Name

Brief description of what this service does.

## Features
- Feature 1
- Feature 2

## Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+

## Setup

### Local Development
# Commands here

## Configuration
Explain environment variables and config files

## Running Tests
pytest -v --cov

## Architecture
Brief explanation of key components
```

### API Documentation (Future Phases)
Link to OpenAPI/Swagger docs for any RESTful APIs developed using FastAPI (if applicable).
```

## Database Conventions

### Naming
- Tables: plural, snake_case (e.g., `bufr_files`, `radar_configurations`)
- Columns: snake_case (e.g., `created_at`, `file_path`)
- Indexes: `idx_{table}_{columns}` (e.g., `idx_bufr_files_radar_datetime`)
- Foreign keys: `fk_{table}_{referenced_table}` (e.g., `fk_bufr_files_radars`)

### Standard Columns
All tables should include:
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at TIMESTAMP NOT NULL DEFAULT NOW(),
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

### Model Example
```python
from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class BUFRFile(Base):
    __tablename__ = "bufr_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    radar_id = Column(UUID(as_uuid=True), ForeignKey("radars.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    strategy = Column(String(50), nullable=False)
    volume = Column(String(10), nullable=False)
    status = Column(Enum(FileStatus), nullable=False, default=FileStatus.PENDING)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    radar = relationship("Radar", back_populates="bufr_files")
    
    # Indexes
    __table_args__ = (
        Index('idx_bufr_files_radar_datetime', 'radar_id', 'datetime'),
        Index('idx_bufr_files_status', 'status'),
    )
```

### Docker conventions
#### Dockerfile best practices
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev --no-root

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "src/main.py"]
```

### docker-compose.yml structure
```yaml
version: '3.9'

services:
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  ingestion:
    build:
      context: ./services/ingestion
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    volumes:
      - bufr_data:/data/bufr
      - ./config:/config:ro
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  bufr_data:
```

## Testing Standards
### Test Structure
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    engine = create_engine("postgresql://test:test@localhost:5432/test_db")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def mock_ftp_client():
    """Mock FTP client for testing."""
    with patch('src.clients.ftp_client.FTP') as mock:
        yield mock

# tests/unit/test_ftp_client.py
import pytest
from src.clients.ftp_client import FTPClient, FTPConnectionError

class TestFTPClient:
    """Test suite for FTP client operations."""
    
    def test_connect_success(self, mock_ftp_client):
        """Test successful FTP connection."""
        client = FTPClient(config)
        assert client.connect() is True
        
    def test_connect_failure(self, mock_ftp_client):
        """Test FTP connection failure handling."""
        mock_ftp_client.side_effect = ConnectionError()
        client = FTPClient(config)
        
        with pytest.raises(FTPConnectionError):
            client.connect()
            
    @pytest.mark.parametrize("path,expected_count", [
        ("/data/2024/01", 5),
        ("/data/2024/02", 10),
        ("/empty", 0),
    ])
    def test_list_files(self, mock_ftp_client, path, expected_count):
        """Test file listing with different paths."""
        client = FTPClient(config)
        files = client.list_files(path)
        assert len(files) == expected_count
```
### Test Coverage Requirements
* Minimum 80% code coverage
* 100% coverage for critical paths (data ingestion, processing)
* All public methods must have tests
* Include integration tests for service interactions

### Running tests
```bash
# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# With coverage
pytest --cov=src --cov-report=html --cov-report=term

# Specific test
pytest tests/unit/test_ftp_client.py::TestFTPClient::test_connect_success -v
```

## Configuration Management
### Configuration File Structure (config.yaml)
```yaml
# FTP Configuration
ftp:
  host: "ftp.example.com"
  port: 21
  username: ${FTP_USERNAME}  # Environment variable
  password: ${FTP_PASSWORD}  # Environment variable
  base_path: "/radar_data"
  timeout: 30
  passive_mode: true

# Radar Configuration
radars:
  - id: "radar_001"
    name: "Buenos Aires"
    enabled: true
    strategies:
      - strategy_id: "0315"
        volumes:
          - number: "01"
            fields: ["DBZH", "KDP", "RHOHV"]
          - number: "02"
            fields: ["VRAD", "WRAD"]

# Database Configuration
database:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}
  name: ${DB_NAME}
  user: ${DB_USER}
  password: ${DB_PASSWORD}
  pool_size: 10
  max_overflow: 20

# Application Configuration
app:
  environment: ${ENVIRONMENT:-development}
  log_level: ${LOG_LEVEL:-INFO}
  polling_interval: 300  # seconds
  max_concurrent_downloads: 5
  retry_max_attempts: 3
  retry_backoff_factor: 2

# Storage Configuration
storage:
  bufr_path: "/data/bufr"
  cog_path: "/data/cogs"
  retention_days: 30
```

### Pydantic Settings Implementation
```python
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path

class FTPConfig(BaseModel):
    host: str
    port: int = 21
    username: str
    password: str
    base_path: str
    timeout: int = 30
    passive_mode: bool = True

class VolumeConfig(BaseModel):
    number: str
    fields: List[str]

class StrategyConfig(BaseModel):
    strategy_id: str
    volumes: List[VolumeConfig]

class RadarConfig(BaseModel):
    id: str
    name: str
    enabled: bool = True
    strategies: List[StrategyConfig]

class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432
    name: str
    user: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class AppConfig(BaseModel):
    environment: str = "development"
    log_level: str = "INFO"
    polling_interval: int = 300
    max_concurrent_downloads: int = 5
    retry_max_attempts: int = 3
    retry_backoff_factor: int = 2

class StorageConfig(BaseModel):
    bufr_path: Path
    cog_path: Path
    retention_days: int = 30
    
    @validator("bufr_path", "cog_path")
    def create_path(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v

class Settings(BaseSettings):
    ftp: FTPConfig
    radars: List[RadarConfig]
    database: DatabaseConfig
    app: AppConfig
    storage: StorageConfig
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        yaml_file = "config.yaml"

# Usage
settings = Settings()
```
## Error Handling Patterns
### Exception Hierarchy
```python
class RadarPlatformError(Exception):
    """Base exception for all radar platform errors."""
    def __init__(self, message: str, details: Optional[dict] = None):
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

class ProcessingError(RadarPlatformError):
    """Base class for processing errors."""
    pass

class BUFRDecodeError(ProcessingError):
    """Raised when BUFR decoding fails."""
    pass

class COGGenerationError(ProcessingError):
    """Raised when COG generation fails."""
    pass
```
### Error Handling Pattern
```python
from typing import Optional
import traceback

def download_with_retry(
    file_path: str,
    max_retries: int = 3
) -> Optional[Path]:
    """Download file with exponential backoff retry."""
    
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            logger.info(
                "download_attempt",
                file_path=file_path,
                attempt=retry_count + 1,
                max_attempts=max_retries
            )
            
            result = ftp_client.download(file_path)
            
            logger.info(
                "download_success",
                file_path=file_path,
                size_bytes=result.size
            )
            
            return result.local_path
            
        except FTPConnectionError as e:
            last_error = e
            logger.warning(
                "download_connection_error",
                file_path=file_path,
                error=str(e),
                retry_count=retry_count
            )
            # Reconnect and retry
            ftp_client.reconnect()
            
        except FTPDownloadError as e:
            last_error = e
            logger.error(
                "download_failed",
                file_path=file_path,
                error=str(e),
                retry_count=retry_count,
                traceback=traceback.format_exc()
            )
            
        except Exception as e:
            # Unexpected error - log and re-raise
            logger.critical(
                "download_unexpected_error",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            raise
        
        retry_count += 1
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # Exponential backoff
            logger.info("retrying_download", wait_seconds=wait_time)
            time.sleep(wait_time)
    
    # All retries exhausted
    logger.error(
        "download_failed_all_retries",
        file_path=file_path,
        total_attempts=max_retries,
        last_error=str(last_error)
    )
    
    return None
```

## Git Workflow
### Branch Naming
* Feature: `feature/short-description`
* Bugfix: `bugfix/short-description`
* Hotfix: `hotfix/short-description`
* Release: `release/v1.0.0`

### Commit Messages
Follow conventional commits:
```text
<type>(<scope>): <subject>

<body>

<footer>
```

Types:

* `feat`: New feature
* `fix`: Bug fix
* `docs`: Documentation changes
* `style`: Code style changes (formatting)
* `refactor`: Code refactoring
* `test`: Adding or updating tests
* `chore`: Maintenance tasks

Example
```text
feat(ingestion): add FTP client with retry logic

Implement FTP client that supports:
- Connection with timeout
- File listing with date filtering
- Download with exponential backoff retry
- Proper error handling and logging

Closes #123
```

## Response Format for Copilot
When I ask you to implement something, please:

1. **Confirm Understanding**
    - Summarize what you're about to build
    - Ask clarifying questions if needed
2. **Propose Approach**
    - Outline the implementation strategy
    - Mention any trade-offs or alternatives
3. **Provide Code**
    - Full, working code with proper structure
    - Include all necessary imports
    - Add comprehensive docstrings
    - Include type hints
4. **Explain Key Decisions**
    - Why you chose a particular approach
    - Any assumptions made
    - Potential gotchas or limitations
5. **Suggest Next Steps**
    - What to test
    - What to build next
    - Any refactoring opportunities

## Example Response Format
```markdown
## Understanding
You want me to implement an FTP client that downloads BUFR files with retry logic and state tracking in the database.

## Approach
I'll create:
1. FTPClient class with connection pooling
2. Retry decorator with exponential backoff
3. Database update methods for status tracking
4. Comprehensive error handling

Trade-off: Using synchronous FTP instead of async for simplicity in MVP phase.

## Implementation

[CODE HERE]

## Key Decisions
- Used ftplib instead of asyncio-ftp for MVP simplicity
- Implemented retry at the method level rather than decorator for better control
- Status updates happen after each operation for real-time tracking

## Testing Suggestions
1. Test with mock FTP server
2. Verify retry logic with intermittent failures
3. Check database status updates
4. Test concurrent downloads

## Next Steps
- Add integration test with real FTP server
- Implement download queue management
- Add Prometheus metrics for monitoring
```

### Questions to Ask Before Implementing
When I request a feature, consider asking:

1. Scope: Should this handle [edge case]?
2. Performance: Do you expect [X] concurrent operations?
3. Error Handling: How should we handle [specific failure scenario]?
4. Configuration: Should [parameter] be configurable?
5. Testing: Do you want unit tests, integration tests, or both?
6. Dependencies: Is it okay to add [library] as a dependency?

### Project Phases Reference
**✅ Phase 1 (Current): Single Radar Ingestion**
- FTP monitoring and download
- Basic state management
- Database schema
- Docker setup

**🔄 Phase 2: BUFR Processing**
- BUFR decoding with eccodes
- Metadata extraction
- Error handling for corrupt files
**📋 Phase 3: COG Generation**
- Raster processing with rasterio
- COG optimization
- Product configuration system
**📋 Phase 4: REST API**
- FastAPI implementation
- Authentication/authorization
- Public vs. paid endpoints
**📋 Phase 5: Frontend**
- React/Vue with TypeScript
- Leaflet map integration
- Animation controls
**📋 Phase 6: Multi-Radar Support**
- Parallel processing
- Radar status dashboard
- Configuration management UI
**📋 Phase 7: Advanced Features**
- User accounts
- Payment integration
- Custom product generation

### When to Wait for Feedback
Pause and ask for feedback after:

- Completing a major component (e.g., FTP client)
- Before adding a new dependency
- When multiple approaches are viable
- After implementing tests
- Before refactoring working code
- When facing an architectural decision

## Common Patterns to Follow
### Async Operations
```python
import asyncio
from typing import List

async def fetch_multiple_files(file_paths: List[str]) -> List[Path]:
    """Download multiple files concurrently."""
    tasks = [download_file(path) for path in file_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successes = [r for r in results if isinstance(r, Path)]
    failures = [r for r in results if isinstance(r, Exception)]
    
    logger.info(
        "batch_download_complete",
        total=len(file_paths),
        successes=len(successes),
        failures=len(failures)
    )
    
    return successes
```

### Context Managers
```python
from contextlib import contextmanager

@contextmanager
def ftp_connection(config: FTPConfig):
    """Context manager for FTP connections."""
    client = FTPClient(config)
    try:
        client.connect()
        yield client
    finally:
        client.disconnect()

# Usage
with ftp_connection(config) as ftp:
    files = ftp.list_files("/data")
```

### Repository Pattern
```python
from sqlalchemy.orm import Session
from typing import List, Optional

class BUFRFileRepository:
    """Repository for BUFR file operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, bufr_file: BUFRFile) -> BUFRFile:
        """Create new BUFR file record."""
        self.session.add(bufr_file)
        self.session.commit()
        self.session.refresh(bufr_file)
        return bufr_file
    
    def get_by_id(self, file_id: UUID) -> Optional[BUFRFile]:
        """Get BUFR file by ID."""
        return self.session.query(BUFRFile).filter(
            BUFRFile.id == file_id
        ).first()
    
    def get_pending_files(
        self,
        radar_id: UUID,
        limit: int = 100
    ) -> List[BUFRFile]:
        """Get pending files for a radar."""
        return self.session.query(BUFRFile).filter(
            BUFRFile.radar_id == radar_id,
            BUFRFile.status == FileStatus.PENDING
        ).limit(limit).all()
    
    def update_status(
        self,
        file_id: UUID,
        status: FileStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update file status."""
        self.session.query(BUFRFile).filter(
            BUFRFile.id == file_id
        ).update({
            "status": status,
            "error_message": error_message,
            "updated_at": datetime.utcnow()
        })
        self.session.commit()
```
## Performance Considerations
### Database Optimization
- Use connection pooling
- Batch inserts when possible
- Create appropriate indexes
- Use EXPLAIN ANALYZE for slow queries
### File Processing
- Process files in batches
- Use multiprocessing for CPU-intensive tasks
- Clean up temporary files promptly
- Monitor disk space
### Memory Management
- Stream large files instead of loading entirely
- Use generators for large datasets
- Close database connections properly
- Profile memory usage regularly
### Security Best Practices
1. Never commit secrets
  - Use environment variables
  - Add .env to .gitignore
  - Use secrets management in production
2. Input Validation
  - Validate all external inputs
  - Use Pydantic models for validation
  - Sanitize file paths
3. Database Security
  - Use parameterized queries (SQLAlchemy handles this)
  - Implement connection encryption
  - Follow principle of least privilege
4. API Security (Future)
  - Implement rate limiting
  - Use HTTPS only
  - Validate JWT tokens
  - Implement CORS properly

## Remember
- Start simple, iterate based on feedback
- Working code > perfect code (in MVP phase)
- Test as you go
- Document why, not just what
- Ask questions when uncertain
- One feature at a time
- Wait for user validation before proceeding