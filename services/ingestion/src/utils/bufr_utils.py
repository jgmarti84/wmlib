"""Utilities for BUFR file handling and radar naming."""
import re
from datetime import datetime, timezone
from typing import Dict, Optional, Pattern
import structlog

logger = structlog.get_logger()

# Pre-compiled regex pattern for BUFR filename parsing
# Format: RADAR_VOLCODE_VOLNR_FIELD_TIMESTAMP.BUFR
# Example: RMA11_0315_01_DBZH_20251120T120000Z.BUFR
BUFR_FILENAME_PATTERN = re.compile(
    r"^([A-Z0-9]+)_(\d{4})_(\d{2})_([A-Z]{2,10})_(\d{8}T\d{6}Z)\.BUFR$",
    re.IGNORECASE
)


def extract_bufr_filename_components(filename: str) -> Dict[str, Optional[str]]:
    """
    Extract radar_name, strategy, vol_nr, and field_type from a BUFR filename.
    
    BUFR filename format: RADAR_VOLCODE_VOLNR_FIELD_TIMESTAMP.BUFR
    Example: RMA11_0315_01_DBZH_20251120T120000Z.BUFR
    
    Args:
        filename: BUFR filename to parse
        
    Returns:
        Dictionary with keys: radar_name, strategy, vol_nr, field_type, timestamp
        Returns None for any key if extraction fails.
        
    Example:
        >>> result = extract_bufr_filename_components('RMA11_0315_01_DBZH_20251120T120000Z.BUFR')
        >>> result
        {'radar_name': 'RMA11', 'strategy': '0315', 'vol_nr': '01', 'field_type': 'DBZH', 'timestamp': '20251120T120000Z'}
    """
    match = BUFR_FILENAME_PATTERN.match(filename)
    
    if match:
        return {
            "radar_name": match.group(1),
            "strategy": match.group(2),
            "vol_nr": match.group(3),
            "field_type": match.group(4),
            "timestamp": match.group(5),
        }
    else:
        return {
            "radar_name": None,
            "strategy": None,
            "vol_nr": None,
            "field_type": None,
            "timestamp": None,
        }


def parse_bufr_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Parse timestamp from BUFR filename.
    
    Args:
        timestamp: Timestamp string in format YYYYMMDDTHHMMSSZ
        
    Returns:
        datetime object with UTC timezone, or None if parsing fails
        
    Example:
        >>> dt = parse_bufr_timestamp('20251120T120000Z')
        >>> dt.isoformat()
        '2025-11-20T12:00:00+00:00'
    """
    try:
        # Format: 20251120T120000Z
        dt = datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError as e:
        logger.warning("failed_to_parse_timestamp", timestamp=timestamp, error=str(e))
        return None


def build_vol_types_regex(vol_types: Dict[str, Dict[str, list]]) -> Optional[Pattern]:
    """
    Build a compiled regex pattern from vol_types dictionary to match BUFR filenames.
    
    The vol_types dictionary structure:
        vol_types['strategy'] = {'vol_nr': ['FIELD1', 'FIELD2', ...], ...}
    
    BUFR filename format: RADAR_VOLCODE_VOLNR_FIELD_TIMESTAMP.BUFR
    
    The regex will match filenames where strategy, vol_nr, and field are all present
    in the vol_types dictionary.
    
    Example:
        >>> vol_types = {
        ...     '0315': {'01': ['DBZH', 'DBZV', 'ZDR', 'RHOHV', 'KDP'], '02': ['VRAD', 'WRAD']},
        ...     '0302': {'01': ['DBZH']}
        ... }
        >>> regex = build_vol_types_regex(vol_types)
        >>> bool(regex.match('RMA11_0315_01_DBZH_20251120T120000Z.BUFR'))
        True
        >>> bool(regex.match('RMA11_0315_01_INVALID_20251120T120000Z.BUFR'))
        False
        
    Args:
        vol_types: Dictionary mapping strategy -> {vol_nr -> [field_names]}
        
    Returns:
        Compiled regex pattern, or None if vol_types is empty.
    """
    if not vol_types:
        return None
    
    # Build list of patterns: strategy_vol_nr_field combinations
    patterns = []
    
    for strategy, vol_numbers in vol_types.items():
        for vol_nr, fields in vol_numbers.items():
            for field in fields:
                # Create pattern: _STRATEGY_VOLNR_FIELD_
                # Using escaped characters to handle special regex chars
                pattern = f"_{re.escape(strategy)}_{re.escape(vol_nr)}_{re.escape(field)}_"
                patterns.append(pattern)
    
    if not patterns:
        return None
    
    # Combine all patterns with OR (|)
    combined_pattern = "|".join(patterns)
    
    # Add anchors: match anywhere in filename and end with .BUFR
    full_pattern = f"^.*(?:{combined_pattern}).*\\.BUFR$"
    
    try:
        return re.compile(full_pattern, re.IGNORECASE)
    except re.error as e:
        logger.error("failed_to_compile_vol_types_regex", error=str(e))
        return None


def get_radar_names() -> Dict[str, str]:
    """
    Get mapping of common radar names used in Argentina.
    
    Returns:
        Dictionary mapping radar IDs to full names
        
    Example radar names from RMA network:
    - RMA1: Ezeiza
    - RMA2: Resistencia
    - RMA3: Paraná
    - RMA4: Córdoba
    - RMA5: Mendoza
    - RMA6: Bariloche
    - RMA7: Termas de Rio Hondo
    - RMA8: Las Lomitas
    - RMA11: Anguil
    """
    return {
        "RMA1": "Ezeiza",
        "RMA2": "Resistencia",
        "RMA3": "Paraná",
        "RMA4": "Córdoba",
        "RMA5": "Mendoza",
        "RMA6": "Bariloche",
        "RMA7": "Termas de Rio Hondo",
        "RMA8": "Las Lomitas",
        "RMA11": "Anguil",
    }


def validate_bufr_filename(filename: str, vol_types: Optional[Pattern] = None) -> bool:
    """
    Validate if a filename matches BUFR pattern and optional vol_types filter.
    
    Args:
        filename: Filename to validate
        vol_types: Optional compiled regex pattern for volume type filtering
        
    Returns:
        True if filename is valid, False otherwise
    """
    # Check basic BUFR pattern
    if not BUFR_FILENAME_PATTERN.match(filename):
        return False
    
    # Check vol_types filter if provided
    if vol_types is not None:
        if not vol_types.match(filename):
            return False
    
    return True
