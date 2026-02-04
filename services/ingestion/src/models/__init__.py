"""Database models base configuration."""
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Import models to ensure they're registered with Base
from src.models.radar import Radar
from src.models.strategy import Strategy, Volume, RadarStrategy
from src.models.bufr_file import BUFRFile, FileStatus

__all__ = ["Base", "Radar", "Strategy", "Volume", "RadarStrategy", "BUFRFile", "FileStatus"]
