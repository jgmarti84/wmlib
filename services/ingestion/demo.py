#!/usr/bin/env python3
"""Demo script to test the ingestion service.

This script demonstrates:
1. Setting up the database with SQLite
2. Initializing radars
3. Checking the database state
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Settings, FTPConfig, DatabaseConfig, AppConfig, StorageConfig, RadarConfig
from src.database.repository import RadarRepository
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
)


def create_test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        ftp=FTPConfig(
            host="test.ftp.server",
            port=21,
            username="testuser",
            password="testpass",
            base_path="/radar_data"
        ),
        radars=[
            RadarConfig(
                id="radar_001",
                name="Test Radar Station",
                enabled=True,
                strategies=[
                    {
                        "strategy_id": "0315",
                        "volumes": [
                            {"number": "01", "fields": ["DBZH", "KDP", "RHOHV"]},
                            {"number": "02", "fields": ["VRAD", "WRAD"]}
                        ]
                    }
                ]
            )
        ],
        database=DatabaseConfig(
            host="localhost",
            port=5432,
            name="wmlib_demo",
            user="demo_user",
            password="demo_pass"
        ),
        app=AppConfig(
            environment="demo",
            log_level="INFO"
        ),
        storage=StorageConfig(
            bufr_path=Path("/tmp/wmlib_demo/bufr"),
            cog_path=Path("/tmp/wmlib_demo/cogs")
        )
    )


def main():
    """Run demo."""
    logger = structlog.get_logger()
    logger.info("wmlib_demo_start")
    
    # Create settings with SQLite for demo
    logger.info("creating_settings")
    
    # Create demo directories
    demo_dir = Path("/tmp/wmlib_demo")
    demo_dir.mkdir(exist_ok=True)
    
    settings = Settings(
        ftp=FTPConfig(
            host="demo.ftp.server",
            port=21,
            username="demo",
            password="demo",
            base_path="/radar_data"
        ),
        radars=[
            RadarConfig(
                id="radar_001",
                name="Demo Radar Station",
                enabled=True,
                strategies=[
                    {
                        "strategy_id": "0315",
                        "volumes": [
                            {"number": "01", "fields": ["DBZH", "KDP", "RHOHV"]},
                            {"number": "02", "fields": ["VRAD", "WRAD"]}
                        ]
                    }
                ]
            )
        ],
        database=DatabaseConfig(
            host="localhost",
            port=5432,
            name="wmlib_demo",
            user="demo_user",
            password="demo_pass"
        ),
        app=AppConfig(
            environment="demo",
            log_level="INFO"
        ),
        storage=StorageConfig(
            bufr_path=demo_dir / "bufr",
            cog_path=demo_dir / "cogs"
        )
    )
    
    # Initialize database with SQLite
    logger.info("initializing_database")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.models import Base
    
    # Use SQLite for demo
    db_path = demo_dir / "demo.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("database_initialized", db_path=str(db_path))
    
    # Initialize radars
    logger.info("initializing_radars")
    with SessionLocal() as session:
        repo = RadarRepository(session)
        
        for radar_config in settings.radars:
            radar = repo.get_by_radar_id(radar_config.id)
            if not radar:
                from src.models.radar import Radar
                radar = Radar(
                    radar_id=radar_config.id,
                    name=radar_config.name,
                    enabled=radar_config.enabled,
                    strategies=[s.model_dump() for s in radar_config.strategies]
                )
                repo.create(radar)
                session.commit()
    
    # Show what's in the database
    logger.info("checking_database")
    with SessionLocal() as session:
        repo = RadarRepository(session)
        radars = repo.get_all_enabled()
        
        logger.info("radars_in_database", count=len(radars))
        for radar in radars:
            logger.info(
                "radar_info",
                radar_id=radar.radar_id,
                name=radar.name,
                strategies=radar.strategies
            )
    
    logger.info(
        "demo_complete",
        message="Service is ready. Database created at " + str(db_path),
        next_steps="Configure FTP credentials in config.yaml and run: python src/main.py --once"
    )


if __name__ == "__main__":
    main()
