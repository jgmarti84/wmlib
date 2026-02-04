"""Integration test for database operations."""
import pytest
from datetime import datetime

from src.models.radar import Radar
from src.models.bufr_file import BUFRFile, FileStatus
from src.database.repository import RadarRepository, BUFRFileRepository


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    def test_create_radar(self, db_session):
        """Test creating a radar in database."""
        repo = RadarRepository(db_session)
        
        radar = Radar(
            radar_id="test_001",
            name="Test Radar",
            enabled=True,
            strategies=[{"strategy_id": "0315", "volumes": []}]
        )
        
        created = repo.create(radar)
        
        assert created.id is not None
        assert created.radar_id == "test_001"
        assert created.name == "Test Radar"
    
    def test_get_radar_by_id(self, db_session):
        """Test retrieving radar by radar_id."""
        repo = RadarRepository(db_session)
        
        radar = Radar(
            radar_id="test_002",
            name="Test Radar 2",
            enabled=True,
            strategies=[]
        )
        created = repo.create(radar)
        db_session.commit()
        
        retrieved = repo.get_by_radar_id("test_002")
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.radar_id == "test_002"
    
    def test_get_all_enabled_radars(self, db_session):
        """Test retrieving all enabled radars."""
        repo = RadarRepository(db_session)
        
        radar1 = Radar(radar_id="r1", name="R1", enabled=True, strategies=[])
        radar2 = Radar(radar_id="r2", name="R2", enabled=False, strategies=[])
        radar3 = Radar(radar_id="r3", name="R3", enabled=True, strategies=[])
        
        repo.create(radar1)
        repo.create(radar2)
        repo.create(radar3)
        db_session.commit()
        
        enabled = repo.get_all_enabled()
        
        assert len(enabled) == 2
        assert all(r.enabled for r in enabled)
    
    def test_create_bufr_file(self, db_session):
        """Test creating BUFR file record."""
        radar_repo = RadarRepository(db_session)
        file_repo = BUFRFileRepository(db_session)
        
        # Create radar first
        radar = Radar(radar_id="r1", name="R1", enabled=True, strategies=[])
        radar_repo.create(radar)
        db_session.commit()
        
        # Create BUFR file
        bufr_file = BUFRFile(
            radar_id=radar.id,
            file_path="/data/test.bufr",
            remote_path="/remote/test.bufr",
            datetime=datetime.utcnow(),
            strategy="0315",
            volume="01",
            status=FileStatus.PENDING
        )
        
        created = file_repo.create(bufr_file)
        
        assert created.id is not None
        assert created.status == FileStatus.PENDING
        assert created.retry_count == 0
    
    def test_update_file_status(self, db_session):
        """Test updating file status."""
        radar_repo = RadarRepository(db_session)
        file_repo = BUFRFileRepository(db_session)
        
        radar = Radar(radar_id="r1", name="R1", enabled=True, strategies=[])
        radar_repo.create(radar)
        db_session.commit()
        
        bufr_file = BUFRFile(
            radar_id=radar.id,
            file_path="/data/test.bufr",
            remote_path="/remote/test.bufr",
            datetime=datetime.utcnow(),
            strategy="0315",
            volume="01",
            status=FileStatus.PENDING
        )
        created = file_repo.create(bufr_file)
        db_session.commit()
        
        # Update status
        file_repo.update_status(created.id, FileStatus.DOWNLOADED)
        db_session.commit()
        
        updated = file_repo.get_by_id(created.id)
        assert updated.status == FileStatus.DOWNLOADED
    
    def test_get_pending_files_for_radar(self, db_session):
        """Test getting pending files for a radar."""
        radar_repo = RadarRepository(db_session)
        file_repo = BUFRFileRepository(db_session)
        
        radar = Radar(radar_id="r1", name="R1", enabled=True, strategies=[])
        radar_repo.create(radar)
        db_session.commit()
        
        # Create multiple files
        for i in range(5):
            bufr_file = BUFRFile(
                radar_id=radar.id,
                file_path=f"/data/test{i}.bufr",
                remote_path=f"/remote/test{i}.bufr",
                datetime=datetime.utcnow(),
                strategy="0315",
                volume="01",
                status=FileStatus.PENDING if i < 3 else FileStatus.DOWNLOADED
            )
            file_repo.create(bufr_file)
        db_session.commit()
        
        pending = file_repo.get_pending_for_radar(radar.id, limit=10)
        
        assert len(pending) == 3
        assert all(f.status == FileStatus.PENDING for f in pending)
