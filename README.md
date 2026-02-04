# WMLib - Meteorological Data Visualization Platform

Production-ready platform for processing and displaying real-time meteorological radar data.

## Overview

WMLib ingests BUFR files from radar stations via FTP, processes them into Cloud Optimized GeoTIFFs (COGs), and serves them through a web interface with animated radar imagery.

Reference implementation: https://webmet.ohmc.ar/

## Current Status: Phase 1 - MVP

✅ **Completed Features:**
- FTP monitoring and download service
- Basic state management with PostgreSQL
- Database schema for radars and BUFR files
- Docker containerization
- Structured logging
- Unit and integration tests

🚧 **Upcoming Phases:**
- Phase 2: BUFR decoding and data processing
- Phase 3: COG generation
- Phase 4: REST API with FastAPI
- Phase 5: Web frontend with real-time visualization

## Technology Stack

- **Backend**: Python 3.11+, FastAPI (future)
- **Database**: PostgreSQL 15+
- **Package Manager**: Poetry
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest
- **Logging**: structlog

## Quick Start

### Prerequisites

- Docker & Docker Compose
- FTP server credentials with radar data

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jgmarti84/wmlib.git
   cd wmlib
   ```

2. **Configure FTP and radar settings**
   ```bash
   # Edit config/config.yaml with your FTP credentials and radar configuration
   nano config/config.yaml
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Monitor logs**
   ```bash
   docker-compose logs -f ingestion
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

## Project Structure

```
wmlib/
├── services/
│   └── ingestion/          # FTP monitoring and download service
│       ├── src/
│       │   ├── clients/    # FTP client
│       │   ├── database/   # Database management
│       │   ├── models/     # SQLAlchemy models
│       │   ├── services/   # Business logic
│       │   ├── utils/      # Utilities
│       │   ├── config.py   # Configuration
│       │   └── main.py     # Entry point
│       ├── tests/          # Test suites
│       ├── Dockerfile
│       ├── pyproject.toml
│       └── README.md
├── config/
│   └── config.yaml         # Application configuration
├── database/
│   └── init.sql           # Database initialization
├── docs/                   # Documentation
├── docker-compose.yml      # Docker orchestration
└── README.md              # This file
```

## Configuration

Main configuration file: `config/config.yaml`

Key sections:
- **FTP**: Server connection settings
- **Radars**: Radar station configurations
- **Database**: PostgreSQL settings
- **App**: Application behavior
- **Storage**: File storage paths

See [services/ingestion/README.md](services/ingestion/README.md) for detailed configuration options.

## Development

### Local Setup

1. **Install Poetry**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**
   ```bash
   cd services/ingestion
   poetry install
   ```

3. **Run tests**
   ```bash
   poetry run pytest -v --cov=src
   ```

4. **Run service locally**
   ```bash
   # Start PostgreSQL
   docker-compose up -d postgres
   
   # Run service
   poetry run python src/main.py --once  # Run once
   poetry run python src/main.py         # Run continuously
   ```

## Testing

```bash
cd services/ingestion

# All tests
poetry run pytest -v

# With coverage
poetry run pytest --cov=src --cov-report=html

# Specific test file
poetry run pytest tests/unit/test_ftp_client.py -v
```

## Architecture

### Phase 1 Architecture

```
┌──────────────┐
│ FTP Server   │
│ (Radar Data) │
└──────┬───────┘
       │
       │ Poll & Download
       │
┌──────▼──────────────┐
│ Ingestion Service   │
│ - FTP monitoring    │
│ - File tracking     │
│ - Download mgmt     │
└──────┬──────────────┘
       │
       │ State Management
       │
┌──────▼──────────────┐
│ PostgreSQL          │
│ - Radar configs     │
│ - File tracking     │
└─────────────────────┘
```

### Future Architecture

Additional components planned:
- BUFR processing service
- COG generation service  
- FastAPI REST API
- Web frontend with Leaflet.js
- Redis for caching and task queue

## Database Schema

### Radars
Stores radar station configurations including strategies and volumes.

### BUFR Files
Tracks file lifecycle: pending → downloading → downloaded → processing → completed/failed

See [services/ingestion/README.md](services/ingestion/README.md) for detailed schema.

## Contributing

This is an MVP implementation following incremental development:
1. Build one feature at a time
2. Test thoroughly before moving forward
3. Keep code simple and maintainable
4. Follow Python best practices

## Documentation

- [Project Context](docs/PROJECT_CONTEXT.md) - Full project overview and guidelines
- [Ingestion Service](services/ingestion/README.md) - Service-specific documentation
- [Copilot Instructions](docs/COPILOT_INSTRUCTION.md) - Development guidelines

## License

TBD

## Acknowledgments

Reference implementation: https://webmet.ohmc.ar/
