"""Test configuration and fixtures."""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLASession

from src.models import Base
from src.config import Settings, FTPConfig, DatabaseConfig, AppConfig, StorageConfig, RadarConfig
from src.database import DatabaseManager


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory):
    """Create test settings."""
    temp_dir = tmp_path_factory.mktemp("data")
    
    return Settings(
        ftp=FTPConfig(
            host="test.ftp.com",
            port=21,
            username="testuser",
            password="testpass",
            base_path="/test"
        ),
        radars=[
            RadarConfig(
                id="test_radar",
                name="Test Radar",
                enabled=True,
                strategies=[]
            )
        ],
        database=DatabaseConfig(
            host="localhost",
            port=5432,
            name="test_db",
            user="test_user",
            password="test_pass"
        ),
        app=AppConfig(
            environment="test",
            log_level="DEBUG"
        ),
        storage=StorageConfig(
            bufr_path=temp_dir / "bufr",
            cog_path=temp_dir / "cogs"
        )
    )


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine with function scope."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def mock_ftp_client():
    """Mock FTP client."""
    mock = MagicMock()
    mock.connect.return_value = True
    mock.is_connected.return_value = True
    mock.list_files.return_value = []
    mock.download_file.return_value = True
    return mock
