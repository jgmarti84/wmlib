# FTP Scanner Implementation Reference

This document explains the FTP scanning implementation based on the radarlib reference.

## FTP Directory Structure

The FTP server follows a hierarchical date-based structure:

```
/{base_path}/{radar_name}/YYYY/MM/DD/HH/MMSS/
```

Example paths:
```
/L2/RMA11/2025/11/20/12/0000/RMA11_0315_01_DBZH_20251120T120000Z.BUFR
/L2/RMA11/2025/11/20/12/0500/RMA11_0315_01_DBZH_20251120T120500Z.BUFR
/L2/RMA1/2025/11/20/14/3022/RMA1_0315_02_VRAD_20251120T143022Z.BUFR
```

- **base_path**: `/L2` (configurable, standard for BUFR Level 2 data)
- **radar_name**: RMA radar identifier (RMA1, RMA11, RMA4, etc.)
- **YYYY/MM/DD/HH**: Standard date/time hierarchy
- **MMSS**: Minute (2 digits) + Second (2 digits), e.g., `0000`, `0500`, `3022`

## BUFR Filename Format

Files follow strict naming convention:

```
{RADAR}_{VOLCODE}_{VOLNR}_{FIELD}_{TIMESTAMP}.BUFR
```

Components:
- **RADAR**: Radar identifier (e.g., `RMA11`, `RMA1`)
- **VOLCODE**: 4-digit strategy/volume code (e.g., `0315`, `0302`)
- **VOLNR**: 2-digit volume number (e.g., `01`, `02`)
- **FIELD**: 2-10 character field type (e.g., `DBZH`, `VRAD`, `RHOHV`)
- **TIMESTAMP**: `YYYYMMDDTHHMMSSZformat (e.g., `20251120T120000Z`)

Examples:
```
RMA11_0315_01_DBZH_20251120T120000Z.BUFR
RMA11_0315_01_ZDR_20251120T120000Z.BUFR
RMA11_0315_02_VRAD_20251120T120000Z.BUFR
RMA1_0302_01_RHOHV_20241115T093000Z.BUFR
```

## Radar Names (RMA Network)

Standard radar identifiers in Argentina's RMA network:

| Radar ID | Location |
|----------|----------|
| RMA1 | Ezeiza |
| RMA2 | Resistencia |
| RMA3 | Paraná |
| RMA4 | Córdoba |
| RMA5 | Mendoza |
| RMA6 | Bariloche |
| RMA7 | Termas de Rio Hondo |
| RMA8 | Las Lomitas |
| RMA11 | Anguil |

## Volume Types Configuration

Volume types define which data to download using a hierarchical structure:

```yaml
radars:
  - id: "RMA11"
    name: "Anguil"
    strategies:
      - strategy_id: "0315"  # Strategy code
        volumes:
          - number: "01"     # Volume number
            fields: ["DBZH", "DBZV", "ZDR", "RHOHV", "PHIDP", "KDP"]
          - number: "02"
            fields: ["VRAD", "WRAD"]
```

This structure filters files by:
1. **Strategy**: The 4-digit volume code (0315, 0302, etc.)
2. **Volume**: The 2-digit volume number within strategy
3. **Fields**: List of field types to download

## Field Types

Common radar data fields:

| Field | Description |
|-------|-------------|
| DBZH | Horizontal reflectivity |
| DBZV | Vertical reflectivity |
| ZDR | Differential reflectivity |
| RHOHV | Correlation coefficient |
| PHIDP | Differential phase |
| KDP | Specific differential phase |
| VRAD | Radial velocity |
| WRAD | Spectral width |

## Implementation Details

### FTP Traversal Method

The `traverse_radar()` method efficiently navigates the hierarchical structure:

1. Start at `/{base_path}/{radar_name}`
2. List and filter year directories
3. For each valid year, list and filter month directories
4. Continue down to day → hour → minute/second
5. At each level, apply datetime range filtering
6. In minute/second directories, list BUFR files
7. Apply volume type regex filtering
8. Validate filename format
9. Yield (datetime, filename, remote_path) tuples

### Volume Type Filtering

The `build_vol_types_regex()` function creates a compiled regex from the configuration:

```python
vol_types = {
    "0315": {
        "01": ["DBZH", "ZDR", "RHOHV"],
        "02": ["VRAD", "WRAD"]
    }
}
```

Becomes regex matching patterns like:
```
_0315_01_DBZH_
_0315_01_ZDR_
_0315_01_RHOHV_
_0315_02_VRAD_
_0315_02_WRAD_
```

This ensures only configured data is downloaded.

### Filename Component Extraction

The `extract_bufr_filename_components()` function parses filenames:

```python
filename = "RMA11_0315_01_DBZH_20251120T120000Z.BUFR"
components = extract_bufr_filename_components(filename)
# Returns:
# {
#     "radar_name": "RMA11",
#     "strategy": "0315",
#     "vol_nr": "01",
#     "field_type": "DBZH",
#     "timestamp": "20251120T120000Z"
# }
```

This information is stored in the database for tracking and processing.

## Configuration Example

Complete example configuration:

```yaml
ftp:
  host: "ftp.smn.gob.ar"
  port: 21
  username: "your_user"
  password: "your_pass"
  base_path: "/L2"
  timeout: 30
  passive_mode: true

radars:
  - id: "RMA11"
    name: "Anguil"
    enabled: true
    strategies:
      - strategy_id: "0315"
        volumes:
          - number: "01"
            fields: ["DBZH", "DBZV", "ZDR", "RHOHV", "PHIDP", "KDP"]
          - number: "02"
            fields: ["VRAD", "WRAD"]
            
  - id: "RMA1"
    name: "Ezeiza"
    enabled: true
    strategies:
      - strategy_id: "0315"
        volumes:
          - number: "01"
            fields: ["DBZH", "KDP", "RHOHV"]
```

## Usage

The ingestion service automatically:

1. Builds volume type regex from configuration
2. Connects to FTP server
3. Calls `traverse_radar()` with date range (default: last hour)
4. Filters files by volume types
5. Tracks new files in database
6. Downloads pending files
7. Updates file status

All based on the proven patterns from radarlib implementation.

## References

- radarlib implementation: https://github.com/jgmarti84/radarlib/tree/main/src/radarlib
- FTP client: `src/radarlib/io/ftp/ftp_client.py`
- Download daemon: `src/radarlib/daemons/download_daemon.py`
- Naming utilities: `src/radarlib/utils/names_utils.py`
