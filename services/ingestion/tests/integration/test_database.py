"""Integration test for database operations."""
import pytest
from datetime import datetime
from decimal import Decimal

from src.models.radar import Radar
from src.models.bufr_file import BUFRFile, FileStatus
from src.database.repository import RadarRepository, BUFRFileRepository


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    def test_create_radar(self, db_session):
        """Test creating a radar in database."""
        repo = RadarRepository(db_session)
        
        radar = Radar(
            code="RMA11",
            title="Test Radar",
            description="Test radar description",
            center_lat=Decimal("-36.5367"),
            center_long=Decimal("-63.9992"),
            is_active=True
        )
        
        created = repo.create(radar)
        
        assert created.code == "RMA11"
        assert created.title == "Test Radar"
        assert created.is_active is True
    
    def test_get_radar_by_code(self, db_session):
        """Test retrieving radar by code."""
        repo = RadarRepository(db_session)
        
        radar = Radar(
            code="RMA1",
            title="Test Radar 2",
            center_lat=Decimal("-34.8222"),
            center_long=Decimal("-58.5358"),
            is_active=True
        )
        created = repo.create(radar)
        db_session.commit()
        
        retrieved = repo.get_by_code("RMA1")
        
        assert retrieved is not None
        assert retrieved.code == created.code
        assert retrieved.code == "RMA1"
    
    def test_get_all_active_radars(self, db_session):
        """Test retrieving all active radars."""
        repo = RadarRepository(db_session)
        
        radar1 = Radar(code="R1", title="R1", center_lat=Decimal("0"), center_long=Decimal("0"), is_active=True)
        radar2 = Radar(code="R2", title="R2", center_lat=Decimal("0"), center_long=Decimal("0"), is_active=False)
        radar3 = Radar(code="R3", title="R3", center_lat=Decimal("0"), center_long=Decimal("0"), is_active=True)
        
        repo.create(radar1)
        repo.create(radar2)
        repo.create(radar3)
        db_session.commit()
        
        active = repo.get_all_active()
        
        assert len(active) == 2
        assert all(r.is_active for r in active)
    
    def test_create_bufr_file(self, db_session):
        """Test creating BUFR file record."""
        radar_repo = RadarRepository(db_session)
        file_repo = BUFRFileRepository(db_session)
        
        # Create radar first
        radar = Radar(code="RMA11", title="R1", center_lat=Decimal("0"), center_long=Decimal("0"), is_active=True)
        radar_repo.create(radar)
        db_session.commit()
        
        # Create BUFR file
        bufr_file = BUFRFile(
            radar_code=radar.code,
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
        
        radar = Radar(code="RMA11", title="R1", center_lat=Decimal("0"), center_long=Decimal("0"), is_active=True)
        radar_repo.create(radar)
        db_session.commit()
        
        bufr_file = BUFRFile(
            radar_code=radar.code,
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
        
        radar = Radar(code="RMA11", title="R1", center_lat=Decimal("0"), center_long=Decimal("0"), is_active=True)
        radar_repo.create(radar)
        db_session.commit()
        
        # Create multiple files
        for i in range(5):
            bufr_file = BUFRFile(
                radar_code=radar.code,
                file_path=f"/data/test{i}.bufr",
                remote_path=f"/remote/test{i}.bufr",
                datetime=datetime.utcnow(),
                strategy="0315",
                volume="01",
                status=FileStatus.PENDING if i < 3 else FileStatus.DOWNLOADED
            )
            file_repo.create(bufr_file)
        db_session.commit()
        
        pending = file_repo.get_pending_for_radar(radar.code, limit=10)
        
        assert len(pending) == 3
        assert all(f.status == FileStatus.PENDING for f in pending)
