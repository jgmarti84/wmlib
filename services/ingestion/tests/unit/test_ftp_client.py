"""Unit tests for FTP client."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from ftplib import error_perm

from src.clients.ftp_client import FTPClient, FTPFileInfo
from src.config import FTPConfig
from src.utils.exceptions import FTPConnectionError, FTPDownloadError, FTPListError


class TestFTPClient:
    """Test suite for FTP client operations."""
    
    def test_init(self):
        """Test FTP client initialization."""
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        
        assert client.config == config
        assert client.ftp is None
        assert not client._connected
    
    @patch('src.clients.ftp_client.FTP')
    def test_connect_success(self, mock_ftp_class):
        """Test successful FTP connection."""
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp
        
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        
        result = client.connect()
        
        assert result is True
        assert client.is_connected()
        mock_ftp.connect.assert_called_once_with("test.com", 21, timeout=30)
        mock_ftp.login.assert_called_once_with("user", "pass")
        mock_ftp.set_pasv.assert_called_once_with(True)
    
    @patch('src.clients.ftp_client.FTP')
    def test_connect_failure(self, mock_ftp_class):
        """Test FTP connection failure."""
        mock_ftp = MagicMock()
        mock_ftp.connect.side_effect = ConnectionError("Connection failed")
        mock_ftp_class.return_value = mock_ftp
        
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        
        with pytest.raises(FTPConnectionError):
            client.connect()
    
    @patch('src.clients.ftp_client.FTP')
    def test_disconnect(self, mock_ftp_class):
        """Test FTP disconnection."""
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp
        
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        client.connect()
        client.disconnect()
        
        assert not client.is_connected()
        mock_ftp.quit.assert_called_once()
    
    @patch('src.clients.ftp_client.FTP')
    def test_list_files_not_connected(self, mock_ftp_class):
        """Test listing files when not connected."""
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        
        with pytest.raises(FTPConnectionError):
            client.list_files("/path")
    
    @patch('src.clients.ftp_client.FTP')
    def test_download_file_success(self, mock_ftp_class, tmp_path):
        """Test successful file download."""
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp
        
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        client.connect()
        
        local_path = tmp_path / "test.bufr"
        
        # Mock the retrbinary to write some data
        def mock_retrbinary(cmd, callback):
            callback(b"test data")
        
        mock_ftp.retrbinary.side_effect = mock_retrbinary
        
        result = client.download_file("/remote/test.bufr", local_path)
        
        assert result is True
        assert local_path.exists()
        mock_ftp.retrbinary.assert_called_once()
    
    @patch('src.clients.ftp_client.FTP')
    def test_download_file_not_connected(self, mock_ftp_class, tmp_path):
        """Test download when not connected."""
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        
        local_path = tmp_path / "test.bufr"
        
        with pytest.raises(FTPConnectionError):
            client.download_file("/remote/test.bufr", local_path)
    
    def test_match_pattern(self):
        """Test pattern matching."""
        config = FTPConfig(
            host="test.com",
            port=21,
            username="user",
            password="pass",
            base_path="/data"
        )
        client = FTPClient(config)
        
        assert client._match_pattern("test.bufr", "*.bufr") is True
        assert client._match_pattern("test.txt", "*.bufr") is False
        assert client._match_pattern("file123.bufr", "file*.bufr") is True
