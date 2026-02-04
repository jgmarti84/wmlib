# Quick Start Guide - WMLib Phase 1

This guide helps you get started with the WMLib FTP ingestion service.

## Prerequisites

- Docker & Docker Compose (recommended)
- OR Python 3.11+ and PostgreSQL 15+ for local development
- FTP server credentials with BUFR radar data

## Option 1: Docker Deployment (Recommended)

### Step 1: Configure FTP Credentials

Edit `config/config.yaml`:

```yaml
ftp:
  host: "your-ftp-server.com"
  port: 21
  username: "your_username"
  password: "your_password"
  base_path: "/path/to/radar/data"
```

### Step 2: Configure Radars

Edit the radars section in `config/config.yaml`:

```yaml
radars:
  - id: "radar_001"
    name: "Your Radar Station Name"
    enabled: true
    strategies:
      - strategy_id: "0315"
        volumes:
          - number: "01"
            fields: ["DBZH", "KDP", "RHOHV"]
          - number: "02"
            fields: ["VRAD", "WRAD"]
```

### Step 3: Start Services

```bash
# Start all services
docker compose up -d

# Check logs
docker compose logs -f ingestion

# Check status
docker compose ps
```

### Step 4: Verify Operation

```bash
# Check PostgreSQL
docker compose exec postgres psql -U wmlib_user -d wmlib -c "SELECT * FROM radars;"

# Check BUFR files being tracked
docker compose exec postgres psql -U wmlib_user -d wmlib -c "SELECT file_path, status FROM bufr_files LIMIT 10;"

# View logs
docker compose logs ingestion | grep file_downloaded
```

### Step 5: Stop Services

```bash
docker compose down
```

## Option 2: Local Development

### Step 1: Install Dependencies

```bash
cd services/ingestion

# Install Python dependencies
pip install sqlalchemy psycopg2-binary pydantic pydantic-settings \
    pyyaml structlog python-dotenv

# OR use the system's package manager
# On Ubuntu/Debian:
# sudo apt-get install python3-sqlalchemy python3-psycopg2 python3-pydantic
```

### Step 2: Start PostgreSQL

```bash
# Using Docker for just PostgreSQL
docker compose up -d postgres

# Or use a local PostgreSQL installation
# sudo systemctl start postgresql
```

### Step 3: Configure Settings

Copy and edit the configuration:

```bash
cp ../../config/config.yaml ./config.yaml
nano config.yaml  # Edit with your settings
```

Or use environment variables:

```bash
cp ../../.env.example .env
nano .env  # Edit with your credentials
```

### Step 4: Run the Service

```bash
cd services/ingestion

# Run once (for testing)
python3 src/main.py --once

# Run continuously (production)
python3 src/main.py
```

## Configuration Guide

### FTP Path Structure

The service expects FTP paths structured as:
```
{base_path}/{radar_id}/{strategy_id}/{volume_number}/
```

Example:
```
/radar_data/radar_001/0315/01/
/radar_data/radar_001/0315/02/
```

Adjust this in `src/services/ingestion_service.py` if your structure is different.

### Polling Interval

Control how often the service checks for new files:

```yaml
app:
  polling_interval: 300  # seconds (5 minutes)
```

### Retry Configuration

Configure retry behavior for failed downloads:

```yaml
app:
  retry_max_attempts: 3      # Max retries per file
  retry_backoff_factor: 2    # Exponential backoff multiplier
```

### Storage Paths

Configure where files are stored:

```yaml
storage:
  bufr_path: "/data/bufr"  # BUFR files
  cog_path: "/data/cogs"   # COG files (future)
  retention_days: 30        # How long to keep files
```

## Testing

### Run Tests

```bash
cd services/ingestion

# All tests
python3 -m pytest tests/ -v

# Just unit tests
python3 -m pytest tests/unit/ -v

# Just integration tests
python3 -m pytest tests/integration/ -v

# With coverage
python3 -m pytest tests/ --cov=src --cov-report=term
```

### Demo Script

Run the demo to verify setup without FTP:

```bash
cd services/ingestion
python3 demo.py
```

This creates a test database and initializes the radar configuration.

## Monitoring

### View Logs

```bash
# Docker
docker compose logs -f ingestion

# Filter for specific events
docker compose logs ingestion | grep file_downloaded
docker compose logs ingestion | grep ERROR
```

### Check Database

```bash
# Docker
docker compose exec postgres psql -U wmlib_user -d wmlib

# Useful queries:
# List all radars
SELECT radar_id, name, enabled FROM radars;

# List pending files
SELECT file_path, status, retry_count FROM bufr_files WHERE status = 'pending' LIMIT 10;

# Count files by status
SELECT status, COUNT(*) FROM bufr_files GROUP BY status;

# Recent downloads
SELECT file_path, file_size, created_at FROM bufr_files 
WHERE status = 'downloaded' 
ORDER BY created_at DESC LIMIT 10;
```

## Troubleshooting

### Can't Connect to FTP

1. Verify credentials in config.yaml
2. Test FTP connection manually:
   ```bash
   ftp your-ftp-server.com
   # Enter username and password
   # Try listing files: ls
   ```
3. Check firewall rules
4. Ensure passive mode is correctly configured

### Database Connection Failed

1. Check PostgreSQL is running:
   ```bash
   docker compose ps postgres
   ```
2. Verify database credentials
3. Test connection:
   ```bash
   docker compose exec postgres psql -U wmlib_user -d wmlib
   ```

### Files Not Downloading

1. Check FTP path structure matches configuration
2. Verify file pattern (*.bufr)
3. Check logs for errors:
   ```bash
   docker compose logs ingestion | grep ERROR
   ```
4. Check database for failed files:
   ```sql
   SELECT file_path, error_message FROM bufr_files WHERE status = 'failed';
   ```

### High Retry Count

If files keep failing:

1. Check FTP server stability
2. Verify network connectivity
3. Check local disk space
4. Review error messages in database

## Common Workflows

### Add a New Radar

1. Edit `config/config.yaml`:
   ```yaml
   radars:
     - id: "radar_002"
       name: "New Radar Station"
       enabled: true
       strategies: [...]
   ```

2. Restart service:
   ```bash
   docker compose restart ingestion
   ```

### Disable a Radar

1. Edit `config/config.yaml`:
   ```yaml
   radars:
     - id: "radar_001"
       enabled: false  # Disable
   ```

2. Restart service

### Clear Old Data

The retention system is not yet implemented. For now, manually:

```sql
-- Delete files older than 30 days
DELETE FROM bufr_files WHERE created_at < NOW() - INTERVAL '30 days';
```

### Reset Everything

```bash
# Stop services
docker compose down

# Remove volumes (CAUTION: Deletes all data)
docker compose down -v

# Start fresh
docker compose up -d
```

## Production Considerations

### Security

1. Never commit `.env` or credentials to git
2. Use environment variables for sensitive data
3. Restrict database access
4. Use secure FTP (FTPS) if available

### Performance

1. Adjust `polling_interval` based on data frequency
2. Monitor disk space for BUFR storage
3. Consider database indexing for large datasets
4. Use Docker resource limits if needed

### Reliability

1. Monitor service health
2. Set up log aggregation (e.g., ELK stack)
3. Configure alerts for failures
4. Regular database backups

## Next Steps

After Phase 1 is working:

- **Phase 2**: BUFR decoding and data extraction
- **Phase 3**: COG generation from BUFR data
- **Phase 4**: REST API with FastAPI
- **Phase 5**: Web frontend with real-time visualization

## Support

- Check logs first: `docker compose logs ingestion`
- Review documentation in `services/ingestion/README.md`
- Open an issue on GitHub with logs and configuration (redact credentials!)

## Example Production Deployment

```bash
# Clone repository
git clone https://github.com/jgmarti84/wmlib.git
cd wmlib

# Configure
cp .env.example .env
nano .env  # Add production credentials
nano config/config.yaml  # Configure radars

# Deploy
docker compose up -d

# Monitor
docker compose logs -f ingestion

# Check health
curl http://localhost:5432  # PostgreSQL should be running
docker compose ps  # All services should be Up and healthy
```

That's it! You now have a working FTP ingestion service for meteorological radar data.
