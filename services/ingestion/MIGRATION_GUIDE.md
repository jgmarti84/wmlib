# Database Migration Guide

## Schema Changes

The database schema has been refactored to support dynamic strategy management. The key changes are:

### Old Schema
- **radars**: Had `id` (UUID) as primary key and stored strategies as JSON

### New Schema
- **radars**: Uses `code` (String) as primary key with location metadata
- **strategies**: Independent table for reusable strategies
- **volumes**: Volume configurations per strategy
- **radar_strategies**: Many-to-many association between radars and strategies
- **bufr_files**: References radar by code instead of UUID

## Migration Options

### Option 1: Automatic Migration (Recommended)

The ingestion service will automatically detect schema incompatibility and migrate:

```bash
# Run with automatic migration detection
docker compose up -d

# Or for local development
cd services/ingestion
poetry run python -m src.main
```

The service will:
1. Check if the existing schema is compatible
2. If incompatible, drop old tables and create new ones
3. Initialize radars from configuration

**⚠️ WARNING**: This will delete all existing data in the old schema.

### Option 2: Force Migration

To explicitly force a migration (useful when schema is partially broken):

```bash
# Using Docker
docker compose run ingestion python -m src.main --migrate

# Or for local development
poetry run python -m src.main --migrate
```

### Option 3: Manual Migration

If you want more control:

1. **Backup existing data** (if needed):
   ```bash
   docker compose exec postgres pg_dump -U radar_user radar_db > backup.sql
   ```

2. **Connect to database**:
   ```bash
   docker compose exec postgres psql -U radar_user -d radar_db
   ```

3. **Drop old tables**:
   ```sql
   DROP TABLE IF EXISTS bufr_files CASCADE;
   DROP TABLE IF EXISTS radars CASCADE;
   ```

4. **Restart the service** to create new tables:
   ```bash
   docker compose restart ingestion
   ```

## Verifying Migration

After migration, verify the new schema:

```bash
# Connect to database
docker compose exec postgres psql -U radar_user -d radar_db

# List tables
\dt

# Check radars table structure
\d radars

# Check radar_strategies association
\d radar_strategies

# Check strategies and volumes
\d strategies
\d volumes
```

Expected tables:
- `radars` - with columns: code, title, description, center_lat, center_long, is_active
- `strategies` - with columns: strategy_id, name, description, is_active
- `volumes` - with columns: id, strategy_id, volume_number, fields, sort_order
- `radar_strategies` - with columns: radar_code, strategy_id, is_active, priority
- `bufr_files` - with column: radar_code (instead of radar_id)

## Troubleshooting

### Error: "column 'code' referenced in foreign key constraint does not exist"

This error occurs when old tables exist. Solutions:

1. **Stop the service**:
   ```bash
   docker compose down
   ```

2. **Remove the database volume** (destroys all data):
   ```bash
   docker volume rm wmlib_postgres_data
   ```

3. **Restart**:
   ```bash
   docker compose up -d
   ```

### Error: "relation 'radars' already exists"

The migration script detected the old schema but failed to drop tables. Try:

```bash
# Force migration
docker compose run ingestion python -m src.main --migrate
```

### Migration succeeds but no radars initialized

Check your `config/config.yaml` file includes radar location metadata:

```yaml
radars:
  - code: "RMA11"
    title: "Anguil"
    description: "Radar station in La Pampa"
    center_lat: -36.5297
    center_long: -63.9958
    is_active: true
    strategies:
      - strategy_id: "0315"
        name: "Standard Volume Scan"
        volumes:
          - number: "01"
            fields: ["DBZH", "DBZV", "ZDR", "RHOHV", "PHIDP", "KDP"]
```

## Post-Migration

After successful migration:

1. **Verify radar initialization**:
   ```bash
   docker compose logs ingestion | grep "radars_initialized"
   ```

2. **Check database state**:
   ```bash
   docker compose exec postgres psql -U radar_user -d radar_db -c "SELECT code, title, is_active FROM radars;"
   ```

3. **Monitor ingestion**:
   ```bash
   docker compose logs -f ingestion
   ```
