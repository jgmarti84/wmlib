# WMLib Ingestion Service

FTP monitoring and download service for meteorological radar data (BUFR files).

## Features

- **FTP Monitoring**: Continuously polls FTP servers for new BUFR files
- **State Management**: Tracks file status (pending, downloading, downloaded, failed) in PostgreSQL
- **Retry Logic**: Automatic retry with exponential backoff for failed downloads
- **Structured Logging**: JSON-formatted logs for easy parsing and monitoring
- **Docker Support**: Fully containerized with Docker Compose

## Prerequisites

- Python 3.11+
- Poetry (for local development)
- Docker & Docker Compose (for containerized deployment)
- PostgreSQL 15+ (provided via Docker)

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/jgmarti84/wmlib.git
   cd wmlib
   ```

2. **Configure FTP credentials**
   
   Edit `config/config.yaml` with your FTP server details:
   ```yaml
   ftp:
     host: "your-ftp-server.com"
     username: "your_username"
     password: "your_password"
     base_path: "/path/to/radar/data"
   ```
   
   Or use environment variables by creating a `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Configure radars**
   
   Edit the `radars` section in `config/config.yaml`:
   ```yaml
   radars:
     - id: "radar_001"
       name: "Your Radar Station"
       enabled: true
       strategies:
         - strategy_id: "0315"
           volumes:
             - number: "01"
               fields: ["DBZH", "KDP", "RHOHV"]
   ```

4. **Start the services**
   ```bash
   docker-compose up -d
   ```

5. **Check logs**
   ```bash
   docker-compose logs -f ingestion
   ```

6. **Stop the services**
   ```bash
   docker-compose down
   ```

## Local Development Setup

1. **Install dependencies**
   ```bash
   cd services/ingestion
   poetry install
   ```

2. **Start PostgreSQL**
   ```bash
   docker-compose up -d postgres
   ```

3. **Configure settings**
   
   Copy the config file and adjust settings:
   ```bash
   cp ../../config/config.yaml ./config.yaml
   # Edit config.yaml
   ```

4. **Run the service**
   ```bash
   poetry run python src/main.py
   ```

5. **Run tests**
   ```bash
   poetry run pytest -v
   ```

## Configuration

### FTP Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `host` | FTP server hostname | - |
| `port` | FTP server port | 21 |
| `username` | FTP username | - |
| `password` | FTP password | - |
| `base_path` | Base path on FTP server | / |
| `timeout` | Connection timeout (seconds) | 30 |
| `passive_mode` | Use passive mode | true |

### Application Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `polling_interval` | FTP polling interval (seconds) | 300 |
| `max_concurrent_downloads` | Max concurrent downloads | 5 |
| `retry_max_attempts` | Max retry attempts | 3 |
| `retry_backoff_factor` | Retry backoff multiplier | 2 |
| `log_level` | Logging level | INFO |

### Storage Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `bufr_path` | Path for BUFR files | /data/bufr |
| `cog_path` | Path for COG files | /data/cogs |
| `retention_days` | Data retention days | 30 |

## Architecture

```
┌─────────────────┐
│  FTP Server     │
└────────┬────────┘
         │
         │ (poll & download)
         │
┌────────▼────────┐
│  FTP Client     │
└────────┬────────┘
         │
┌────────▼────────────┐
│ Ingestion Service   │
│  - Scan FTP         │
│  - Track files      │
│  - Download files   │
│  - Update status    │
└────────┬────────────┘
         │
         │ (state management)
         │
┌────────▼────────┐
│   PostgreSQL    │
│  - Radars       │
│  - BUFR Files   │
└─────────────────┘
```

## Database Schema

### Radars Table
- `id` (UUID): Primary key
- `radar_id` (String): Unique radar identifier
- `name` (String): Radar station name
- `enabled` (Boolean): Whether radar is active
- `strategies` (JSON): Strategies configuration
- `created_at`, `updated_at` (DateTime): Timestamps

### BUFR Files Table
- `id` (UUID): Primary key
- `radar_id` (UUID): Foreign key to radars
- `file_path` (String): Local file path
- `remote_path` (String): Remote FTP path
- `datetime` (DateTime): File datetime
- `strategy` (String): Strategy identifier
- `volume` (String): Volume number
- `status` (Enum): File status (pending, downloading, downloaded, failed)
- `retry_count` (Integer): Number of retry attempts
- `error_message` (Text): Error details if failed
- `file_size` (Integer): File size in bytes
- `created_at`, `updated_at` (DateTime): Timestamps

## Testing

Run all tests:
```bash
cd services/ingestion
poetry run pytest -v
```

Run with coverage:
```bash
poetry run pytest --cov=src --cov-report=html --cov-report=term
```

Run specific test:
```bash
poetry run pytest tests/unit/test_ftp_client.py -v
```

## Troubleshooting

### Connection Issues

If you can't connect to FTP server:
1. Verify FTP credentials in config
2. Check firewall rules
3. Ensure passive mode is correctly configured
4. Check logs: `docker-compose logs ingestion`

### Database Issues

If database connection fails:
1. Ensure PostgreSQL is running: `docker-compose ps`
2. Check database credentials
3. Verify network connectivity: `docker-compose exec ingestion ping postgres`

### File Download Issues

If files fail to download:
1. Check FTP path structure matches configuration
2. Verify file permissions on local storage
3. Check retry count and error messages in database
4. Review logs for detailed error information

## Monitoring

The service logs structured JSON for easy parsing. Key log events:

- `ingestion_iteration_start` / `ingestion_iteration_complete`
- `ftp_connected` / `ftp_disconnected`
- `radar_processing_complete`
- `file_downloaded`
- `file_download_failed`

Example log query (using jq):
```bash
docker-compose logs ingestion | grep file_downloaded | jq '.'
```

## Next Steps

Phase 1 provides the foundation for:
- Phase 2: BUFR decoding and processing
- Phase 3: COG generation
- Phase 4: Web API and frontend
- Phase 5: Real-time visualization

## License

TBD

## Support

For issues and questions, please open an issue on GitHub.
