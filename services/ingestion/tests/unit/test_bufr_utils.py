"""Unit tests for BUFR utilities."""
import pytest
from datetime import datetime, timezone

from src.utils.bufr_utils import (
    extract_bufr_filename_components,
    parse_bufr_timestamp,
    build_vol_types_regex,
    validate_bufr_filename,
    get_radar_names
)


class TestExtractBufrFilenameComponents:
    """Tests for BUFR filename component extraction."""
    
    def test_valid_filename(self):
        """Test extraction from valid BUFR filename."""
        filename = "RMA11_0315_01_DBZH_20251120T120000Z.BUFR"
        result = extract_bufr_filename_components(filename)
        
        assert result["radar_name"] == "RMA11"
        assert result["strategy"] == "0315"
        assert result["vol_nr"] == "01"
        assert result["field_type"] == "DBZH"
        assert result["timestamp"] == "20251120T120000Z"
    
    def test_lowercase_extension(self):
        """Test with lowercase .bufr extension."""
        filename = "RMA1_0302_02_VRAD_20241115T093000Z.bufr"
        result = extract_bufr_filename_components(filename)
        
        assert result["radar_name"] == "RMA1"
        assert result["strategy"] == "0302"
        assert result["vol_nr"] == "02"
        assert result["field_type"] == "VRAD"
    
    def test_invalid_filename(self):
        """Test with invalid filename format."""
        filename = "invalid_file.bufr"
        result = extract_bufr_filename_components(filename)
        
        assert result["radar_name"] is None
        assert result["strategy"] is None
        assert result["vol_nr"] is None
        assert result["field_type"] is None
        assert result["timestamp"] is None
    
    def test_different_field_types(self):
        """Test with various field types."""
        test_cases = [
            ("RMA11_0315_01_DBZH_20251120T120000Z.BUFR", "DBZH"),
            ("RMA11_0315_01_ZDR_20251120T120000Z.BUFR", "ZDR"),
            ("RMA11_0315_01_RHOHV_20251120T120000Z.BUFR", "RHOHV"),
            ("RMA11_0315_02_VRAD_20251120T120000Z.BUFR", "VRAD"),
            ("RMA11_0315_01_KDP_20251120T120000Z.BUFR", "KDP"),
        ]
        
        for filename, expected_field in test_cases:
            result = extract_bufr_filename_components(filename)
            assert result["field_type"] == expected_field


class TestParseBufrTimestamp:
    """Tests for BUFR timestamp parsing."""
    
    def test_valid_timestamp(self):
        """Test parsing valid timestamp."""
        timestamp = "20251120T120000Z"
        dt = parse_bufr_timestamp(timestamp)
        
        assert dt.year == 2025
        assert dt.month == 11
        assert dt.day == 20
        assert dt.hour == 12
        assert dt.minute == 0
        assert dt.second == 0
        assert dt.tzinfo == timezone.utc
    
    def test_different_times(self):
        """Test parsing various valid timestamps."""
        test_cases = [
            ("20240101T000000Z", (2024, 1, 1, 0, 0, 0)),
            ("20241231T235959Z", (2024, 12, 31, 23, 59, 59)),
            ("20250615T143022Z", (2025, 6, 15, 14, 30, 22)),
        ]
        
        for timestamp, expected in test_cases:
            dt = parse_bufr_timestamp(timestamp)
            assert dt.year == expected[0]
            assert dt.month == expected[1]
            assert dt.day == expected[2]
            assert dt.hour == expected[3]
            assert dt.minute == expected[4]
            assert dt.second == expected[5]
    
    def test_invalid_timestamp(self):
        """Test parsing invalid timestamp."""
        timestamp = "invalid"
        dt = parse_bufr_timestamp(timestamp)
        
        assert dt is None


class TestBuildVolTypesRegex:
    """Tests for volume types regex builder."""
    
    def test_single_strategy_volume(self):
        """Test with single strategy and volume."""
        vol_types = {
            "0315": {"01": ["DBZH", "ZDR"]}
        }
        regex = build_vol_types_regex(vol_types)
        
        assert regex is not None
        assert regex.match("RMA11_0315_01_DBZH_20251120T120000Z.BUFR")
        assert regex.match("RMA11_0315_01_ZDR_20251120T120000Z.BUFR")
        assert not regex.match("RMA11_0315_01_KDP_20251120T120000Z.BUFR")
    
    def test_multiple_strategies_volumes(self):
        """Test with multiple strategies and volumes."""
        vol_types = {
            "0315": {
                "01": ["DBZH", "ZDR", "RHOHV"],
                "02": ["VRAD", "WRAD"]
            },
            "0302": {
                "01": ["DBZH"]
            }
        }
        regex = build_vol_types_regex(vol_types)
        
        assert regex is not None
        assert regex.match("RMA11_0315_01_DBZH_20251120T120000Z.BUFR")
        assert regex.match("RMA11_0315_02_VRAD_20251120T120000Z.BUFR")
        assert regex.match("RMA11_0302_01_DBZH_20251120T120000Z.BUFR")
        assert not regex.match("RMA11_0302_02_VRAD_20251120T120000Z.BUFR")
    
    def test_empty_vol_types(self):
        """Test with empty vol_types."""
        vol_types = {}
        regex = build_vol_types_regex(vol_types)
        
        assert regex is None
    
    def test_case_insensitive(self):
        """Test case insensitive matching."""
        vol_types = {
            "0315": {"01": ["DBZH"]}
        }
        regex = build_vol_types_regex(vol_types)
        
        assert regex.match("RMA11_0315_01_DBZH_20251120T120000Z.BUFR")
        assert regex.match("rma11_0315_01_dbzh_20251120t120000z.bufr")


class TestValidateBufrFilename:
    """Tests for BUFR filename validation."""
    
    def test_valid_filename_no_filter(self):
        """Test valid filename without vol_types filter."""
        filename = "RMA11_0315_01_DBZH_20251120T120000Z.BUFR"
        assert validate_bufr_filename(filename) is True
    
    def test_invalid_filename_no_filter(self):
        """Test invalid filename without vol_types filter."""
        filename = "invalid_file.bufr"
        assert validate_bufr_filename(filename) is False
    
    def test_valid_filename_with_filter_match(self):
        """Test valid filename with matching vol_types filter."""
        filename = "RMA11_0315_01_DBZH_20251120T120000Z.BUFR"
        vol_types = {"0315": {"01": ["DBZH"]}}
        regex = build_vol_types_regex(vol_types)
        
        assert validate_bufr_filename(filename, regex) is True
    
    def test_valid_filename_with_filter_no_match(self):
        """Test valid filename with non-matching vol_types filter."""
        filename = "RMA11_0315_01_KDP_20251120T120000Z.BUFR"
        vol_types = {"0315": {"01": ["DBZH"]}}
        regex = build_vol_types_regex(vol_types)
        
        assert validate_bufr_filename(filename, regex) is False


class TestGetRadarNames:
    """Tests for radar name mapping."""
    
    def test_get_radar_names(self):
        """Test that radar names are returned."""
        names = get_radar_names()
        
        assert isinstance(names, dict)
        assert "RMA1" in names
        assert "RMA11" in names
        assert names["RMA1"] == "Ezeiza"
        assert names["RMA11"] == "Anguil"
